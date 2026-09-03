"""Tests for bridge-side FPHA numerical conditioning."""

from __future__ import annotations

import sys
from pathlib import Path
from types import SimpleNamespace

import pyarrow as pa
import pyarrow.parquet as pq
import pytest

from cobre_bridge.numeric_hardening import (
    FPHA_GAMMA_V_SNAP_EPS,
    has_computed_fpha,
    materialize_hardened_fpha,
)


def _models(source: str = "computed") -> dict[str, object]:
    return {
        "production_models": [
            {
                "hydro_id": 7,
                "selection_mode": "stage_ranges",
                "stage_ranges": [
                    {
                        "model": "fpha",
                        "fpha_config": {
                            "source": source,
                            "fitting_window": {
                                "volume_min_hm3": 10.0,
                                "volume_max_hm3": 20.0,
                            },
                        },
                    }
                ],
            }
        ]
    }


def test_has_computed_fpha_finds_nested_configs() -> None:
    assert has_computed_fpha(_models()) is True
    assert has_computed_fpha(_models("precomputed")) is False


def test_materialize_snaps_only_noise_band_and_selects_precomputed(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    case_dir = tmp_path / "case"
    case_dir.mkdir()
    captured: dict[str, object] = {}

    class FakeStudy:
        def __init__(
            self,
            case_dir: str,
            *,
            output_dir: str,
            threads: int,
            config_overrides: dict[str, object],
        ) -> None:
            captured.update(
                case_dir=case_dir,
                output_dir=output_dir,
                threads=threads,
                config_overrides=config_overrides,
            )

        def train(self) -> None:
            output = Path(str(captured["output_dir"])) / "hydro_models"
            output.mkdir(parents=True)
            pq.write_table(
                pa.table(
                    {
                        "gamma_v": pa.array(
                            [
                                0.0,
                                FPHA_GAMMA_V_SNAP_EPS,
                                -FPHA_GAMMA_V_SNAP_EPS / 2,
                                FPHA_GAMMA_V_SNAP_EPS * 10,
                            ],
                            type=pa.float64(),
                        ),
                        "gamma_q": pa.array([0.2, 0.3, 0.4, 0.5]),
                    }
                ),
                output / "fpha_hyperplanes.parquet",
            )

    monkeypatch.setitem(sys.modules, "cobre", SimpleNamespace(Study=FakeStudy))

    source = _models()
    result = materialize_hardened_fpha(case_dir, source)

    assert captured["case_dir"] == str(case_dir)
    assert captured["threads"] == 1
    assert captured["config_overrides"] == {
        "training.stopping_rules": [{"type": "iteration_limit", "limit": 0}]
    }
    assert result.hyperplanes["gamma_v"].to_pylist() == [
        0.0,
        0.0,
        0.0,
        pytest.approx(1e-9),
    ]
    assert result.hyperplanes["gamma_q"].to_pylist() == [0.2, 0.3, 0.4, 0.5]
    assert result.snapped_gamma_v == 2
    assert result.smallest_retained_gamma_v == pytest.approx(1e-9)

    # The caller's in-memory document is untouched; the result carries the final
    # supported precomputed contract and no computed-only fitting window.
    assert has_computed_fpha(source) is True
    assert has_computed_fpha(result.production_models) is False
    config = result.production_models["production_models"][0]["stage_ranges"][0][
        "fpha_config"
    ]
    assert config == {"source": "precomputed"}


def test_materialize_rejects_missing_generated_artifact(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    class FakeStudy:
        def __init__(self, *_args: object, **_kwargs: object) -> None:
            pass

        def train(self) -> None:
            pass

    monkeypatch.setitem(sys.modules, "cobre", SimpleNamespace(Study=FakeStudy))
    with pytest.raises(RuntimeError, match="produced no FPHA hyperplane artifact"):
        materialize_hardened_fpha(tmp_path, _models())


def test_materialize_rejects_case_without_computed_fpha(tmp_path: Path) -> None:
    with pytest.raises(ValueError, match="without computed FPHA"):
        materialize_hardened_fpha(tmp_path, _models("precomputed"))
