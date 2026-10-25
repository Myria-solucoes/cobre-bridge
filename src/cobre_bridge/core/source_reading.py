"""Encoding-safe adapters for text readers supplied by source-model libraries.

Some upstream block and section readers reuse partial parser state after a late
decode failure. This module selects an encoding against the complete byte stream
and invokes the parser exactly once, without loading the whole file into memory.
"""

from __future__ import annotations

import codecs
from pathlib import Path
from typing import Any

_DECODE_CHUNK_SIZE = 64 * 1024


def _select_encoding(path: Path, encodings: list[str]) -> str:
    decode_error: UnicodeDecodeError | None = None
    for encoding in encodings:
        decoder = codecs.getincrementaldecoder(encoding)(errors="strict")
        try:
            with path.open("rb") as stream:
                while chunk := stream.read(_DECODE_CHUNK_SIZE):
                    decoder.decode(chunk)
                decoder.decode(b"", final=True)
        except UnicodeDecodeError as exc:
            decode_error = exc
            continue
        return encoding
    if decode_error is not None:
        raise decode_error
    raise ValueError("text reader has no configured encoding")


def read_text_file(reader: Any, path: Path, *args: Any, **kwargs: Any) -> Any:
    """Parse *path* after selecting one complete-file-compatible encoding."""
    if not isinstance(reader, type) or not path.is_file():
        return reader.read(str(path), *args, **kwargs)
    configured = getattr(reader, "ENCODING", "utf-8")
    encodings = [configured] if isinstance(configured, str) else list(configured)
    encoding = _select_encoding(path, encodings)
    single_encoding_reader = type(
        f"_SingleEncoding{reader.__name__}",
        (reader,),
        {"ENCODING": encoding},
    )
    return single_encoding_reader.read(str(path), *args, **kwargs)
