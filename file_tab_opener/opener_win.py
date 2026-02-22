"""
Open folders as tabs in Windows Explorer.

Three-tier fallback:
1. pywinauto UIA (Ctrl+T -> UIA address bar input -> Enter)
2. ctypes SendInput (Ctrl+T -> Ctrl+L -> keystroke input -> Enter)
3. Separate windows (subprocess, not tabs)

Note: pywinauto must NOT be imported at module level.
Its comtypes initializes COM as MTA, which conflicts with tkinter's
filedialog (requires STA), causing freezes. Import lazily when needed.
"""

from __future__ import annotations

import ctypes
import ctypes.wintypes as wintypes
import logging
import os
import subprocess
import time
from collections.abc import Callable

log = logging.getLogger(__name__)

# --- Timeout constants ---
_WINDOW_FIND_TIMEOUT = 10.0  # Max wait for new Explorer window detection (seconds)
_WINDOW_FIND_TIMEOUT_SHORT = 5.0  # Shorter timeout for single/separate windows

# --- ctypes SendInput constants and structures ---
INPUT_KEYBOARD = 1
KEYEVENTF_KEYUP = 0x0002
KEYEVENTF_UNICODE = 0x0004

VK_CONTROL = 0x11
VK_RETURN = 0x0D
VK_T = 0x54
VK_L = 0x4C


class KEYBDINPUT(ctypes.Structure):
    _fields_ = [
        ("wVk", wintypes.WORD),
        ("wScan", wintypes.WORD),
        ("dwFlags", wintypes.DWORD),
        ("time", wintypes.DWORD),
        ("dwExtraInfo", ctypes.POINTER(ctypes.c_ulong)),
    ]


class _INPUT_UNION(ctypes.Union):
    # Padding must be large enough for the largest union member (MOUSEINPUT).
    # On 64-bit Windows: sizeof(MOUSEINPUT) = 32, sizeof(KEYBDINPUT) = 24,
    # sizeof(HARDWAREINPUT) = 8.  We only use KEYBDINPUT but the union size
    # must match the C INPUT structure (40 bytes total = 4 byte type + 4 pad
    # + 32 byte union on 64-bit, or 28 bytes total on 32-bit).
    # Using 32 bytes covers both architectures safely.
    _fields_ = [("ki", KEYBDINPUT), ("_padding", ctypes.c_byte * 32)]


class INPUT(ctypes.Structure):
    _fields_ = [("type", wintypes.DWORD), ("union", _INPUT_UNION)]


def _make_key_input(vk: int, flags: int = 0) -> INPUT:
    """Create a keyboard input structure for a virtual key."""
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = vk
    inp.union.ki.dwFlags = flags
    return inp


def _make_unicode_input(char: str, flags: int = 0) -> INPUT:
    """Create a Unicode character input structure."""
    inp = INPUT()
    inp.type = INPUT_KEYBOARD
    inp.union.ki.wVk = 0
    inp.union.ki.wScan = ord(char)
    inp.union.ki.dwFlags = KEYEVENTF_UNICODE | flags
    return inp


def _send_inputs(*inputs: INPUT) -> None:
    """Send keyboard inputs via the SendInput API."""
    arr = (INPUT * len(inputs))(*inputs)
    ctypes.windll.user32.SendInput(len(arr), arr, ctypes.sizeof(INPUT))


def _send_key_combo(vk_modifier: int, vk_key: int) -> None:
    """Send a modifier+key combo (e.g., Ctrl+T)."""
    _send_inputs(
        _make_key_input(vk_modifier),
        _make_key_input(vk_key),
        _make_key_input(vk_key, KEYEVENTF_KEYUP),
        _make_key_input(vk_modifier, KEYEVENTF_KEYUP),
    )


def _type_string(text: str) -> None:
    """Type a string by sending Unicode key events for each character."""
    for char in text:
        _send_inputs(
            _make_unicode_input(char),
            _make_unicode_input(char, KEYEVENTF_KEYUP),
        )


def _press_key(vk: int) -> None:
    """Press and release a single key."""
    _send_inputs(
        _make_key_input(vk),
        _make_key_input(vk, KEYEVENTF_KEYUP),
    )


# --- Window utility functions ---

def _enum_explorer_hwnds() -> list[int]:
    """Enumerate all Explorer window handles (CabinetWClass) via EnumWindows."""
    hwnds: list[int] = []
    WNDENUMPROC = ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)

    def callback(hwnd: int, _lparam: int) -> bool:
        buf = ctypes.create_unicode_buffer(256)
        ctypes.windll.user32.GetClassNameW(hwnd, buf, 256)
        if buf.value == "CabinetWClass":
            hwnds.append(hwnd)
        return True

    ctypes.windll.user32.EnumWindows(WNDENUMPROC(callback), 0)
    return hwnds


def _find_new_explorer_hwnd(
    before_hwnds: list[int], timeout: float = 10.0
) -> int | None:
    """Wait for a new Explorer window that was not in before_hwnds."""
    before_set = set(before_hwnds)
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        for hwnd in _enum_explorer_hwnds():
            if hwnd not in before_set:
                log.debug("New Explorer window found: hwnd=%s (%.1fs)",
                          hwnd, time.monotonic() - start)
                return hwnd
        time.sleep(0.2)
    log.warning("New Explorer window not found (timeout=%.1fs)", timeout)
    return None


def _bring_to_foreground(hwnd: int) -> None:
    """Bring a window to the foreground."""
    ctypes.windll.user32.ShowWindow(hwnd, 9)  # SW_RESTORE
    ctypes.windll.user32.SetForegroundWindow(hwnd)


def _apply_window_rect(hwnd: int, window_rect: tuple[int, int, int, int]) -> None:
    """Move and resize a window to the specified (x, y, width, height)."""
    x, y, w, h = window_rect
    ctypes.windll.user32.MoveWindow(hwnd, x, y, w, h, True)
    log.debug("Applied window rect: hwnd=%s, x=%d, y=%d, w=%d, h=%d", hwnd, x, y, w, h)


def _is_explorer_hwnd(hwnd: int) -> bool:
    """Check if a window handle belongs to an Explorer window (CabinetWClass)."""
    buf = ctypes.create_unicode_buffer(256)
    ctypes.windll.user32.GetClassNameW(hwnd, buf, 256)
    return buf.value == "CabinetWClass"


def get_frontmost_explorer_rect() -> tuple[int, int, int, int] | None:
    """Get the frontmost Explorer window's position and size.

    Returns (x, y, width, height) or None if no Explorer window is found.

    Strategy:
    1. Check if the current foreground window is an Explorer window.
    2. If not, fall back to the first window from _enum_explorer_hwnds().
    """
    # Try the foreground window first
    fg_hwnd = ctypes.windll.user32.GetForegroundWindow()
    if fg_hwnd and _is_explorer_hwnd(fg_hwnd):
        hwnd = fg_hwnd
    else:
        # Fall back to any Explorer window
        hwnds = _enum_explorer_hwnds()
        if not hwnds:
            log.debug("No Explorer window found")
            return None
        hwnd = hwnds[0]

    rect = wintypes.RECT()
    if not ctypes.windll.user32.GetWindowRect(hwnd, ctypes.byref(rect)):
        log.warning("GetWindowRect failed for hwnd=%s", hwnd)
        return None

    x, y = rect.left, rect.top
    w, h = rect.right - rect.left, rect.bottom - rect.top
    log.debug("Explorer rect: hwnd=%s, x=%d, y=%d, w=%d, h=%d", hwnd, x, y, w, h)
    return (x, y, w, h)


def _wait_for_navigation(addr_edit: object, timeout: float = 30.0) -> bool:
    """
    Wait for navigation to complete.

    After pressing Enter, poll the address bar Edit control's keyboard
    focus. When it loses focus, navigation is complete (breadcrumb view
    is restored).
    """
    start = time.monotonic()
    while time.monotonic() - start < timeout:
        try:
            if not addr_edit.has_keyboard_focus():
                elapsed = time.monotonic() - start
                log.debug("Navigation complete (%.1fs)", elapsed)
                # Brief additional wait for rendering
                time.sleep(0.3)
                return True
        except Exception:
            # Control not found = breadcrumb view restored
            elapsed = time.monotonic() - start
            log.debug("Address bar Edit disappeared, navigation assumed complete (%.1fs)", elapsed)
            time.sleep(0.3)
            return True
        time.sleep(0.1)

    log.warning("Navigation timeout (%.1fs)", timeout)
    return False


# --- Public interface ---

# Re-export from package root (shared with opener_mac)
from file_tab_opener import validate_paths as validate_paths  # noqa: F401


def open_single_folder(
    path: str,
    window_rect: tuple[int, int, int, int] | None = None,
) -> bool:
    """Open a single folder in a new Explorer window."""
    try:
        before_hwnds = _enum_explorer_hwnds() if window_rect else []
        subprocess.Popen(["explorer.exe", os.path.normpath(path)])
        if window_rect:
            hwnd = _find_new_explorer_hwnd(before_hwnds, timeout=_WINDOW_FIND_TIMEOUT_SHORT)
            if hwnd:
                _apply_window_rect(hwnd, window_rect)
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
    Open multiple folders as tabs in a single Explorer window.

    Fallback order: pywinauto UIA -> ctypes SendInput -> separate windows
    """
    if not paths:
        return False

    paths = list(dict.fromkeys(paths))

    log.info("Opening as tabs: %d paths, timeout=%.0fs", len(paths), timeout)
    for i, p in enumerate(paths):
        log.debug("  [%d] %s", i, p)

    # pywinauto UIA method (direct address bar input, most reliable)
    if _check_pywinauto():
        try:
            return _open_tabs_pywinauto_uia(
                paths, on_progress, on_error, timeout=timeout, window_rect=window_rect,
            )
        except Exception as e:
            log.warning("pywinauto UIA failed: %s", e)

    # ctypes SendInput fallback
    try:
        return _open_tabs_ctypes(paths, on_progress, on_error, timeout=timeout, window_rect=window_rect)
    except Exception as e:
        log.warning("ctypes SendInput failed: %s", e)

    # Final fallback: separate windows (not tabs)
    log.info("Opening as separate windows (fallback)")
    return _open_tabs_separate(paths, on_progress, on_error, window_rect=window_rect)


def _check_pywinauto() -> bool:
    """Check if pywinauto is available (without importing it)."""
    try:
        import importlib.util
        return importlib.util.find_spec("pywinauto") is not None
    except Exception:
        return False


def _open_tabs_pywinauto_uia(
    paths: list[str],
    on_progress: Callable[[int, int, str], None] | None = None,
    on_error: Callable[[str, str], None] | None = None,
    timeout: float = 30.0,
    window_rect: tuple[int, int, int, int] | None = None,
) -> bool:
    """
    Open tabs using pywinauto UIA with direct address bar text input.

    Opens the first path via explorer.exe, connects via UIA, then
    uses Ctrl+T for new tabs and sets the address bar text via
    UIA ValuePattern.
    """
    from pywinauto import Application, keyboard as pwa_keyboard

    log.info("Using pywinauto UIA method")

    # Record existing Explorer windows before opening
    before_hwnds = _enum_explorer_hwnds()
    log.debug("Existing Explorer windows: %d", len(before_hwnds))

    # Open the first path
    first_path = os.path.normpath(paths[0])
    subprocess.Popen(["explorer.exe", first_path])
    log.debug("Launched explorer.exe: %s", first_path)

    # Wait for the new window to appear
    find_timeout = min(timeout, _WINDOW_FIND_TIMEOUT)
    new_hwnd = _find_new_explorer_hwnd(before_hwnds, timeout=find_timeout)
    if not new_hwnd:
        raise RuntimeError("New Explorer window not found")

    if on_progress:
        on_progress(1, len(paths), paths[0])

    if len(paths) == 1:
        return True

    # Connect to the Explorer window via UIA
    app = Application(backend="uia").connect(handle=new_hwnd)
    win = app.window(handle=new_hwnd)
    win.set_focus()
    log.debug("Connected via UIA: hwnd=%s", new_hwnd)

    # Get reference to the address bar Edit control
    addr_edit = win.child_window(
        auto_id="PART_AutoSuggestBox",
        control_type="Group",
    ).child_window(
        auto_id="TextBox",
        control_type="Edit",
    )

    # Open remaining paths: Ctrl+T -> UIA text input -> Enter -> wait
    for i, path in enumerate(paths[1:], start=2):
        try:
            norm_path = os.path.normpath(path)
            log.debug("Adding tab: [%d/%d] %s", i, len(paths), norm_path)

            # Ctrl+T: open a new tab
            pwa_keyboard.send_keys("^t")
            time.sleep(0.8)

            # Set path with retry: Ctrl+L -> input -> verify -> Enter
            path_set = False
            for attempt in range(3):
                # Ctrl+L: focus the address bar
                pwa_keyboard.send_keys("^l")

                # Wait for the address bar Edit to be ready
                try:
                    addr_edit.wait("ready", timeout=3)
                    log.debug("Address bar Edit ready (attempt %d)", attempt + 1)
                except Exception:
                    log.debug("Address bar wait failed (attempt %d), waiting 0.5s", attempt + 1)
                    time.sleep(0.5)

                # Set path via UIA ValuePattern
                try:
                    addr_edit.set_edit_text(norm_path)
                    log.debug("Path set via UIA ValuePattern (attempt %d)", attempt + 1)
                except Exception as uia_e:
                    # Fallback to keyboard input if UIA fails
                    log.debug("UIA input failed (%s), falling back to keyboard", uia_e)
                    pwa_keyboard.send_keys(
                        norm_path, with_spaces=True, pause=0.01
                    )

                time.sleep(0.15)

                # Verify the address bar contains the expected path
                try:
                    current_text = addr_edit.get_value()
                    if current_text and os.path.normpath(current_text) == norm_path:
                        log.debug("Path verified OK: %s", current_text)
                        path_set = True
                        break
                    else:
                        log.warning(
                            "Path mismatch (attempt %d): expected=%s, got=%s",
                            attempt + 1, norm_path, current_text,
                        )
                except Exception as ve:
                    log.debug("Could not verify path (attempt %d): %s", attempt + 1, ve)
                    # If verification fails, assume it's set and proceed
                    path_set = True
                    break

                time.sleep(0.3)

            if not path_set:
                log.warning("Path set failed after retries, proceeding anyway: %s", norm_path)

            time.sleep(0.1)
            # Press Enter to navigate
            pwa_keyboard.send_keys("{ENTER}")

            # Wait for navigation to complete
            _wait_for_navigation(addr_edit, timeout=timeout)

            if on_progress:
                on_progress(i, len(paths), path)

        except Exception as e:
            log.error("Tab addition failed: %s -> %s", path, e)
            if on_error:
                on_error(path, str(e))

    if window_rect:
        _apply_window_rect(new_hwnd, window_rect)

    return True


def _open_tabs_ctypes(
    paths: list[str],
    on_progress: Callable[[int, int, str], None] | None = None,
    on_error: Callable[[str, str], None] | None = None,
    timeout: float = 30.0,
    window_rect: tuple[int, int, int, int] | None = None,
) -> bool:
    """Open tabs using ctypes SendInput (keystroke-based, less reliable)."""
    log.info("Using ctypes SendInput method")

    # Record existing Explorer windows
    before_hwnds = _enum_explorer_hwnds()

    # Open the first path
    subprocess.Popen(["explorer.exe", os.path.normpath(paths[0])])
    time.sleep(1.5)

    if on_progress:
        on_progress(1, len(paths), paths[0])

    if len(paths) == 1:
        return True

    # Bring the new Explorer window to the foreground
    find_timeout = min(timeout, _WINDOW_FIND_TIMEOUT)
    hwnd = _find_new_explorer_hwnd(before_hwnds, timeout=find_timeout)
    if not hwnd:
        raise RuntimeError("New Explorer window not found")
    _bring_to_foreground(hwnd)
    time.sleep(0.3)

    for i, path in enumerate(paths[1:], start=2):
        try:
            log.debug("SendInput: [%d/%d] %s", i, len(paths), path)
            # Ctrl+T: new tab
            _send_key_combo(VK_CONTROL, VK_T)
            time.sleep(0.5)
            # Ctrl+L: focus address bar
            _send_key_combo(VK_CONTROL, VK_L)
            time.sleep(0.3)
            # Type the path
            _type_string(os.path.normpath(path))
            time.sleep(0.1)
            # Enter
            _press_key(VK_RETURN)
            time.sleep(0.8)
            if on_progress:
                on_progress(i, len(paths), path)
        except Exception as e:
            log.error("SendInput failed: %s -> %s", path, e)
            if on_error:
                on_error(path, str(e))

    if window_rect:
        _apply_window_rect(hwnd, window_rect)

    return True


def _open_tabs_separate(
    paths: list[str],
    on_progress: Callable[[int, int, str], None] | None = None,
    on_error: Callable[[str, str], None] | None = None,
    window_rect: tuple[int, int, int, int] | None = None,
) -> bool:
    """Fallback: open each folder in a separate window."""
    for i, path in enumerate(paths, start=1):
        try:
            before_hwnds = _enum_explorer_hwnds() if window_rect else []
            subprocess.Popen(["explorer.exe", os.path.normpath(path)])
            if window_rect:
                hwnd = _find_new_explorer_hwnd(before_hwnds, timeout=_WINDOW_FIND_TIMEOUT_SHORT)
                if hwnd:
                    _apply_window_rect(hwnd, window_rect)
            if on_progress:
                on_progress(i, len(paths), path)
            time.sleep(0.3)
        except Exception as e:
            if on_error:
                on_error(path, str(e))
    return True
