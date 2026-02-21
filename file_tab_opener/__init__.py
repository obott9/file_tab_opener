"""File Tab Opener -- Open multiple folders as tabs in Explorer/Finder."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from importlib.metadata import version

    __version__ = version("file-tab-opener")
except Exception:
    __version__ = "1.0.0"


def validate_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    """Validate paths. Returns (valid_paths, invalid_paths)."""
    valid: list[str] = []
    invalid: list[str] = []
    for p in paths:
        expanded = os.path.expanduser(p)
        if Path(expanded).is_dir():
            valid.append(expanded)
        else:
            invalid.append(p)
    return valid, invalid
