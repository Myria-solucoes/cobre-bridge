"""DECOMP writer for ``constraints/generic_parameters.json``.

Every ``@name`` token of a generic constraint must be declared in the
parameters file or cobre fails to load the case. The RHE constraints read the
per-hydro stored-energy parameters (:mod:`cobre_bridge.core.stored_energy`),
a per-stage limit fraction for a percentage limit, and the expression
parameters of a cascade split between two REEs.

Entry-building delegates to the model-agnostic
:func:`cobre_bridge.cobre.scalar_parameters.build_scalar_parameters`.
"""

from __future__ import annotations

from collections.abc import Iterable, Mapping, Sequence
from pathlib import Path

from cobre_bridge.cobre.case_writer import CaseWriter
from cobre_bridge.cobre.scalar_parameters import build_scalar_parameters

_SCALAR_PARAMETERS_RELPATH = Path("constraints") / "generic_parameters.json"


def build_decomp_scalar_parameters(
    hydro_ids: Iterable[int],
    per_stage: Mapping[str, Sequence[float]] | None = None,
    expressions: Mapping[str, str] | None = None,
) -> dict:
    """Return the ``generic_parameters.json`` dict for a DECOMP case.

    *hydro_ids* are cobre 0-based hydro ids; *per_stage* and *expressions*
    are the RHE parameters (see
    :func:`~cobre_bridge.cobre.scalar_parameters.build_scalar_parameters`).
    """
    return build_scalar_parameters(
        hydro_ids, per_stage=per_stage, expressions=expressions
    )


def write_scalar_parameters(writer: CaseWriter, params: Mapping[str, object]) -> None:
    """Write *params* to ``constraints/generic_parameters.json`` via *writer*."""
    writer.write_json(_SCALAR_PARAMETERS_RELPATH.as_posix(), params)
