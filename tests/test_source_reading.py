"""Tests for the single-pass source text reader."""

from __future__ import annotations

import ast
from pathlib import Path

import pytest

from cobre_bridge.source_reading import read_text_file


class _Reader:
    ENCODING = ["utf-8", "latin-1", "ascii"]

    @classmethod
    def read(cls, content: str, marker: str = "") -> tuple[str | list[str], str, str]:
        return cls.ENCODING, content, marker


def test_read_text_file_selects_one_encoding_and_forwards_arguments(
    tmp_path: Path,
) -> None:
    path = tmp_path / "input.dat"
    path.write_bytes("início\nfinal\n".encode("latin-1"))

    encoding, content, marker = read_text_file(_Reader, path, marker="ok")

    assert encoding == "latin-1"
    assert content == str(path)
    assert marker == "ok"


def test_read_text_file_rejects_bytes_outside_configured_encodings(
    tmp_path: Path,
) -> None:
    class AsciiReader(_Reader):
        ENCODING = ["ascii"]

    path = tmp_path / "input.dat"
    path.write_bytes(b"\xff")

    with pytest.raises(UnicodeDecodeError):
        read_text_file(AsciiReader, path)


def test_read_text_file_preserves_reader_content_fallback_for_missing_path(
    tmp_path: Path,
) -> None:
    path = tmp_path / "missing.dat"

    encoding, content, marker = read_text_file(_Reader, path, marker="fallback")

    assert encoding == _Reader.ENCODING
    assert content == str(path)
    assert marker == "fallback"


def test_text_reader_paths_use_the_single_pass_adapter() -> None:
    source_root = Path(__file__).parents[1] / "src" / "cobre_bridge"
    allowed_binary_readers = {"Cortesh", "Hidr", "Mlt", "Vazoes"}
    violations: list[str] = []

    for path in source_root.rglob("*.py"):
        if path.name == "source_reading.py":
            continue
        tree = ast.parse(path.read_text(encoding="utf-8"), filename=str(path))
        for node in ast.walk(tree):
            if not isinstance(node, ast.Call) or not node.args:
                continue
            function = node.func
            first_arg = node.args[0]
            if not (
                isinstance(function, ast.Attribute)
                and function.attr == "read"
                and isinstance(function.value, ast.Name)
                and isinstance(first_arg, ast.Call)
                and isinstance(first_arg.func, ast.Name)
                and first_arg.func.id == "str"
            ):
                continue
            if function.value.id not in allowed_binary_readers:
                violations.append(f"{path.relative_to(source_root)}:{node.lineno}")

    assert violations == []
