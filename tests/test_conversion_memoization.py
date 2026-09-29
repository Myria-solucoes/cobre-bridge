"""Per-case memoization and the vectorized vazoes.dat reader keep outputs exact."""

from __future__ import annotations

from pathlib import Path

import pandas as pd
import pytest
from inewave.newave import Vazoes

from cobre_bridge.case import NewaveCase, memoize_on_case
from cobre_bridge.converters.hydro.overrides import _apply_permanent_overrides
from cobre_bridge.converters.stochastic import read_vazoes_history


def test_vectorized_vazoes_matches_inewave(newave_mini_deck: Path) -> None:
    path = newave_mini_deck / "vazoes.dat"
    expected = Vazoes.read(path).vazoes.reset_index(drop=True)
    pd.testing.assert_frame_equal(
        read_vazoes_history(path), expected, check_index_type=False
    )


def test_partial_vazoes_record_keeps_inewave_behaviour(tmp_path: Path) -> None:
    path = tmp_path / "vazoes.dat"
    path.write_bytes(b"\x01\x00\x00\x00" * 10)
    try:
        expected: object = Vazoes.read(path).vazoes
    except Exception as exc:  # noqa: BLE001 - mirrors whatever inewave raises
        with pytest.raises(type(exc)):
            read_vazoes_history(path)
    else:
        pd.testing.assert_frame_equal(read_vazoes_history(path), expected)


def test_memoize_on_case_computes_once_and_tolerates_plain_objects() -> None:
    calls: list[int] = []

    class Holder:
        pass

    holder = Holder()
    assert memoize_on_case(holder, "k", lambda: calls.append(1) or 7) == 7
    assert memoize_on_case(holder, "k", lambda: calls.append(1) or 8) == 7
    assert calls == [1]
    assert memoize_on_case(object(), "k", lambda: 9) == 9


def test_permanent_overrides_hand_out_independent_copies(
    newave_mini_deck: Path,
) -> None:
    case = NewaveCase.from_directory(newave_mini_deck)
    cadastro = case.hidr.cadastro
    first = _apply_permanent_overrides(cadastro, case)
    second = _apply_permanent_overrides(cadastro, case)
    pd.testing.assert_frame_equal(first, second)
    if case.modif is not None:
        assert first is not second
        first.iloc[0, 0] = first.iloc[0, 0]  # caller mutation stays local
        column = first.columns[-1]
        first[column] = None
        assert not _apply_permanent_overrides(cadastro, case)[column].isna().all()
