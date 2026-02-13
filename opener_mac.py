"""
Open folders as tabs in macOS Finder.

Two-tier fallback:
1. AppleScript + System Events (⌘T keystroke -> set target)
2. Separate windows (open command, not tabs)

Note: System Events requires Accessibility permission.
"""

from __future__ import annotations

import logging
import os
import subprocess
import time
from collections.abc import Callable
from pathlib import Path

log = logging.getLogger(__name__)


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


def open_single_folder(path: str) -> bool:
    """Open a single folder in a new Finder window."""
    try:
        expanded = os.path.expanduser(path)
        subprocess.Popen(["open", expanded])
        return True
    except OSError:
        return False


def open_folders_as_tabs(
    paths: list[str],
    on_progress: Callable[[int, int, str], None] | None = None,
    on_error: Callable[[str, str], None] | None = None,
) -> bool:
    """
    Open multiple folders as tabs in a single Finder window.

    Fallback order: AppleScript + System Events -> separate windows
    """
    if not paths:
        return False

    log.info("Opening as tabs: %d paths", len(paths))
    for i, p in enumerate(paths):
        log.debug("  [%d] %s", i, p)

    expanded = [os.path.expanduser(p) for p in paths]

    try:
        script = _build_applescript(expanded)
        log.debug("Running AppleScript (%d lines)", script.count("\n") + 1)
        success, error_msg = _run_applescript(script)
        if success:
            log.info("AppleScript succeeded")
            if on_progress:
                for i, p in enumerate(expanded, start=1):
                    on_progress(i, len(expanded), p)
            return True
        else:
            log.warning("AppleScript failed: %s", error_msg)
            if on_error:
                if "assistive" in error_msg.lower():
                    on_error(
                        expanded[0],
                        "Accessibility permission required.\n"
                        "Go to System Settings → Privacy & Security → Accessibility\n"
                        "and enable access for Terminal.app.",
                    )
                else:
                    on_error(expanded[0], f"AppleScript error: {error_msg}")
    except Exception as e:
        log.warning("AppleScript exception: %s", e)
        if on_error:
            on_error(expanded[0], str(e))

    # Fallback: open each folder in a separate window
    log.info("Opening as separate windows (fallback)")
    return _open_separate(expanded, on_progress, on_error)


def _build_applescript(paths: list[str]) -> str:
    """Build an AppleScript to open folders as Finder tabs."""

    def esc(p: str) -> str:
        """Escape backslashes and double quotes for AppleScript strings."""
        return p.replace("\\", "\\\\").replace('"', '\\"')

    lines: list[str] = []
    # First path: open in a new Finder window
    lines.append('tell application "Finder"')
    lines.append("  activate")
    lines.append(f'  open POSIX file "{esc(paths[0])}" as alias')
    lines.append("end tell")
    lines.append("")
    lines.append("delay 0.5")

    # Remaining paths: ⌘T for new tab, then set target
    for path in paths[1:]:
        lines.append("")
        lines.append('tell application "System Events"')
        lines.append('  tell process "Finder"')
        lines.append('    keystroke "t" using command down')
        lines.append("  end tell")
        lines.append("end tell")
        lines.append("")
        lines.append("delay 0.3")
        lines.append("")
        lines.append('tell application "Finder"')
        lines.append(
            f'  set target of front Finder window to POSIX file "{esc(path)}" as alias'
        )
        lines.append("end tell")
        lines.append("")
        lines.append("delay 0.3")

    return "\n".join(lines)


def _run_applescript(script: str) -> tuple[bool, str]:
    """Execute an AppleScript via osascript. Returns (success, error_message)."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=30,
        )
        return result.returncode == 0, result.stderr.strip()
    except subprocess.TimeoutExpired:
        return False, "AppleScript execution timed out"
    except FileNotFoundError:
        return False, "osascript not found (not macOS?)"


def _open_separate(
    paths: list[str],
    on_progress: Callable[[int, int, str], None] | None = None,
    on_error: Callable[[str, str], None] | None = None,
) -> bool:
    """Fallback: open each folder in a separate window."""
    for i, path in enumerate(paths, start=1):
        try:
            subprocess.Popen(["open", path])
            log.debug("Opened separately: [%d/%d] %s", i, len(paths), path)
            if on_progress:
                on_progress(i, len(paths), path)
            time.sleep(0.3)
        except Exception as e:
            log.error("Failed to open: %s -> %s", path, e)
            if on_error:
                on_error(path, str(e))
    return True
