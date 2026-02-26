"""File Tab Opener -- Open multiple folders as tabs in Explorer/Finder."""

from __future__ import annotations

import os
from pathlib import Path

try:
    from importlib.metadata import version

    __version__ = version("file-tab-opener")
except Exception:
    __version__ = "1.1.4"


def is_unc_path(p: str) -> bool:
    """Check if a path is a UNC network path (\\\\server\\share)."""
    normalized = p.replace("/", "\\")
    return normalized.startswith("\\\\")


def validate_paths(paths: list[str]) -> tuple[list[str], list[str]]:
    """Validate paths. Returns (valid_paths, invalid_paths).

    UNC paths (\\\\server\\share) skip the is_dir() check because
    they may require authentication that only Explorer can trigger.
    """
    valid: list[str] = []
    invalid: list[str] = []
    for p in paths:
        expanded = os.path.expanduser(p)
        if is_unc_path(expanded) or Path(expanded).is_dir():
            valid.append(expanded)
        else:
            invalid.append(p)
    return valid, invalid
