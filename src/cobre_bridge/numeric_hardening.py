"""Numerical hardening for converted Cobre cases.

Computed FPHA hyperplanes are deterministic products of the converted geometry,
but convex-hull round-off can leave coefficients that are structurally zero at
magnitudes around ``1e-21``.  Those values are harmless to the physical model and
harmful to LP column scaling.  This module materialises the computed planes once,
snaps only that separated numerical-noise band, and returns a case representation
that uses Cobre's supported ``precomputed`` source contract.
"""

from __future__ import annotations

import copy
import logging
import tempfile
from dataclasses import dataclass
from pathlib import Path

import pyarrow as pa
import pyarrow.parquet as pq

from cobre_bridge import diagnostics as dx
from cobre_bridge.case_writer import CaseWriter

_LOG = logging.getLogger(__name__)

# Cobre accepts gamma_v down to -1e-10 as numerical noise.  Use the same symmetric
# band for both signs so a coefficient cannot survive merely because hull round-off
# happened to be positive.  In the production case that exposed this issue the
# noise cluster ends below 1e-18; the smallest retained value is >9e-9, leaving
# a conservative separation of more than two orders of magnitude.
FPHA_GAMMA_V_SNAP_EPS = 1e-10


@dataclass(frozen=True)
class FphaHardeningResult:
    """Final precomputed FPHA table and its auditable conditioning statistics."""

    hyperplanes: pa.Table
    production_models: dict[str, object]
    snapped_gamma_v: int
    smallest_retained_gamma_v: float | None


def harden_case_fpha(writer: CaseWriter, production_models: dict[str, object]) -> None:
    """Publish portable FPHA planes through the shared conversion writer."""
    if not has_computed_fpha(production_models):
        return
    if writer.dry_run:
        writer.would_write.append(writer.dst / "system/fpha_hyperplanes.parquet")
        return
    hardened = materialize_hardened_fpha(writer.dst, production_models)
    writer.write_parquet("system/fpha_hyperplanes.parquet", hardened.hyperplanes)
    writer.write_json("system/hydro_production_models.json", hardened.production_models)
    dx.emit(
        dx.Diagnostic(
            code="fpha-numerical-hardening",
            severity=dx.Severity.INFO,
            category="Hydro production",
            title="FPHA hyperplanes numerically hardened",
            summary=(
                f"Materialized {hardened.hyperplanes.num_rows} computed FPHA "
                f"hyperplane row(s) and snapped {hardened.snapped_gamma_v} "
                "structurally-zero gamma_v coefficient(s) before selecting "
                "the precomputed source."
            ),
            notes=[
                "Snap threshold: |gamma_v| <= 1e-10 MW/hm3.",
                (
                    "Smallest retained |gamma_v|: "
                    f"{hardened.smallest_retained_gamma_v:.6g} MW/hm3."
                    if hardened.smallest_retained_gamma_v is not None
                    else "No non-zero gamma_v coefficient was retained."
                ),
            ],
        ),
        logger=_LOG,
    )


def has_computed_fpha(value: object) -> bool:
    """Return whether a production-model document contains computed FPHA."""
    if isinstance(value, dict):
        config = value.get("fpha_config")
        if isinstance(config, dict) and config.get("source") == "computed":
            return True
        return any(has_computed_fpha(child) for child in value.values())
    if isinstance(value, list):
        return any(has_computed_fpha(child) for child in value)
    return False


def _use_precomputed_fpha(value: object) -> None:
    """Patch computed FPHA configs in a copied JSON-like object in place."""
    if isinstance(value, dict):
        config = value.get("fpha_config")
        if isinstance(config, dict) and config.get("source") == "computed":
            # fitting_window only belongs to the computed path.  The generated
            # stage-specific rows already encode its result exactly.
            value["fpha_config"] = {"source": "precomputed"}
        for child in value.values():
            _use_precomputed_fpha(child)
    elif isinstance(value, list):
        for child in value:
            _use_precomputed_fpha(child)


def _snap_gamma_v(table: pa.Table) -> tuple[pa.Table, int, float | None]:
    """Snap the Cobre-approved numerical-noise band in ``gamma_v`` to zero."""
    if "gamma_v" not in table.column_names:
        raise ValueError("generated FPHA hyperplanes are missing the gamma_v column")

    values = table["gamma_v"].to_pylist()
    hardened: list[float] = []
    snapped = 0
    retained: list[float] = []
    for raw in values:
        if raw is None:
            raise ValueError("generated FPHA hyperplanes contain a null gamma_v")
        value = float(raw)
        if value != 0.0 and abs(value) <= FPHA_GAMMA_V_SNAP_EPS:
            value = 0.0
            snapped += 1
        elif value != 0.0:
            retained.append(abs(value))
        hardened.append(value)

    index = table.schema.get_field_index("gamma_v")
    result = table.set_column(
        index,
        table.schema.field(index),
        pa.array(hardened, type=pa.float64()),
    )
    return result, snapped, min(retained) if retained else None


def materialize_hardened_fpha(
    case_dir: Path,
    production_models: dict[str, object],
) -> FphaHardeningResult:
    """Materialise, condition, and select precomputed FPHA for ``case_dir``.

    The input case must already have been written with ``source: computed``.  A
    zero-iteration Cobre study performs only deterministic preprocessing and writes
    the exact hyperplanes; no forward/backward solve is executed.  All temporary
    policy and diagnostic artifacts are isolated in a temporary directory.
    """
    if not has_computed_fpha(production_models):
        raise ValueError("FPHA hardening requested for a case without computed FPHA")

    try:
        import cobre  # type: ignore[import-untyped]
    except ImportError as exc:  # pragma: no cover - required runtime dependency
        raise RuntimeError("cobre-python is required for FPHA hardening") from exc

    with tempfile.TemporaryDirectory(prefix="cobre-bridge-fpha-") as raw_tmp:
        output_dir = Path(raw_tmp)
        try:
            study = cobre.Study(
                str(case_dir),
                output_dir=str(output_dir),
                threads=1,
                config_overrides={
                    "training.stopping_rules": [{"type": "iteration_limit", "limit": 0}]
                },
            )
            study.train()
        except Exception as exc:  # noqa: BLE001
            raise RuntimeError(
                f"failed to materialize computed FPHA hyperplanes: {exc}"
            ) from exc

        hyperplane_path = output_dir / "hydro_models" / "fpha_hyperplanes.parquet"
        if not hyperplane_path.is_file():
            raise RuntimeError(
                "Cobre preprocessing produced no FPHA hyperplane artifact"
            )
        hyperplanes = pq.read_table(hyperplane_path)

    if hyperplanes.num_rows == 0:
        raise RuntimeError(
            "Cobre preprocessing produced an empty FPHA hyperplane table"
        )

    hyperplanes, snapped, smallest_retained = _snap_gamma_v(hyperplanes)
    patched = copy.deepcopy(production_models)
    _use_precomputed_fpha(patched)
    if has_computed_fpha(patched):  # defensive recursion-contract assertion
        raise AssertionError("computed FPHA source survived the precomputed rewrite")

    return FphaHardeningResult(
        hyperplanes=hyperplanes,
        production_models=patched,
        snapped_gamma_v=snapped,
        smallest_retained_gamma_v=smallest_retained,
    )
