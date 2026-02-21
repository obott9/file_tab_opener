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

log = logging.getLogger(__name__)

# --- Constants ---
_APPLESCRIPT_TIMEOUT = 30  # osascript execution timeout (seconds)
_RETRY_MAX = 30            # max retries for set target (30 x 0.1s = 3s)
_RETRY_DELAY = 0.1         # delay between retries (seconds)
_ACCESSIBILITY_KEYWORDS = ("assistive", "アクセシビリティ", "辅助功能", "보조")


def _esc_applescript(p: str) -> str:
    """Escape backslashes and double quotes for AppleScript string literals."""
    return p.replace("\\", "\\\\").replace('"', '\\"')


def _build_open_window_script(
    path: str,
    window_rect: tuple[int, int, int, int] | None = None,
) -> str:
    """Build AppleScript to open a single folder in a new Finder window."""
    escaped = _esc_applescript(path)
    script = (
        'tell application "Finder"\n'
        '  activate\n'
        f'  make new Finder window to POSIX file "{escaped}" as alias\n'
    )
    if window_rect:
        x, y, w, h = window_rect
        script += f'  set bounds of front Finder window to {{{x}, {y}, {x + w}, {y + h}}}\n'
    script += 'end tell'
    return script


# Re-export from package root (shared with opener_win)
from file_tab_opener import validate_paths as validate_paths  # noqa: F401


def open_single_folder(
    path: str,
    window_rect: tuple[int, int, int, int] | None = None,
) -> bool:
    """Open a single folder in a new Finder window.

    Uses AppleScript to always create a new window.
    The `open` command reuses an existing Finder window if the folder
    is already open, which is not the desired behavior.
    """
    try:
        expanded = os.path.expanduser(path)
        script = _build_open_window_script(expanded, window_rect)
        # Fire-and-forget: Popen is intentional here. We don't need to wait
        # for the Finder window to appear before returning to the caller.
        subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        return True
    except OSError:
        return False


def open_folders_as_tabs(
    paths: list[str],
    on_progress: Callable[[int, int, str], None] | None = None,
    on_error: Callable[[str, str], None] | None = None,
    timeout: float = 30.0,
    window_rect: tuple[int, int, int, int] | None = None,
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

    script = _build_applescript(expanded, window_rect=window_rect)
    log.debug("Running AppleScript (%d lines)", script.count("\n") + 1)
    try:
        success, error_msg = _run_applescript(script, timeout=timeout)
        if success:
            log.info("AppleScript succeeded")
            if on_progress:
                for i, p in enumerate(expanded, start=1):
                    on_progress(i, len(expanded), p)
            return True
        else:
            log.warning("AppleScript failed: %s", error_msg)
            if on_error:
                if any(kw in error_msg.lower() for kw in _ACCESSIBILITY_KEYWORDS):
                    from file_tab_opener.i18n import t
                    on_error(expanded[0], t("error.accessibility_required"))
                else:
                    on_error(expanded[0], f"AppleScript error: {error_msg}")
    except Exception as e:
        log.warning("AppleScript exception: %s", e)
        if on_error:
            on_error(expanded[0], str(e))

    # Fallback: open each folder in a separate window
    log.info("Opening as separate windows (fallback)")
    return _open_separate(expanded, on_progress, on_error, window_rect=window_rect)


def _build_applescript(
    paths: list[str],
    window_rect: tuple[int, int, int, int] | None = None,
) -> str:
    """Build an AppleScript to open folders as Finder tabs.

    Uses retry loops instead of fixed delays: after ⌘T, repeatedly
    attempts `set target` until it succeeds (max _RETRY_MAX x _RETRY_DELAY).
    This adapts to Mac speed — fast Macs proceed immediately, slow Macs
    wait only as long as needed.
    """
    lines: list[str] = []
    # First path: always create a new Finder window (not reuse existing)
    lines.append('tell application "Finder"')
    lines.append("  activate")
    lines.append(f'  make new Finder window to POSIX file "{_esc_applescript(paths[0])}" as alias')
    if window_rect:
        x, y, w, h = window_rect
        lines.append(f"  set bounds of front Finder window to {{{x}, {y}, {x + w}, {y + h}}}")
    lines.append("end tell")

    # Remaining paths: ⌘T for new tab, then retry set target until ready
    for path in paths[1:]:
        escaped = _esc_applescript(path)
        lines.append("")
        lines.append('tell application "System Events"')
        lines.append('  tell process "Finder"')
        lines.append('    keystroke "t" using command down')
        lines.append("  end tell")
        lines.append("end tell")
        lines.append("")
        lines.append(f"repeat {_RETRY_MAX} times")
        lines.append("  try")
        lines.append('    tell application "Finder"')
        lines.append(
            f'      set target of front Finder window to POSIX file "{escaped}" as alias'
        )
        lines.append("    end tell")
        lines.append("    exit repeat")
        lines.append("  on error")
        lines.append(f"    delay {_RETRY_DELAY}")
        lines.append("  end try")
        lines.append("end repeat")

    return "\n".join(lines)


def _run_applescript(script: str, timeout: float = _APPLESCRIPT_TIMEOUT) -> tuple[bool, str]:
    """Execute an AppleScript via osascript. Returns (success, error_message)."""
    try:
        result = subprocess.run(
            ["osascript", "-e", script],
            capture_output=True,
            text=True,
            timeout=timeout,
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
    window_rect: tuple[int, int, int, int] | None = None,
) -> bool:
    """Fallback: open each folder in a separate new window."""
    for i, path in enumerate(paths, start=1):
        try:
            script = _build_open_window_script(path, window_rect)
            subprocess.Popen(["osascript", "-e", script], stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            log.debug("Opened separately: [%d/%d] %s", i, len(paths), path)
            if on_progress:
                on_progress(i, len(paths), path)
            time.sleep(0.3)
        except Exception as e:
            log.error("Failed to open: %s -> %s", path, e)
            if on_error:
                on_error(path, str(e))
    return True
