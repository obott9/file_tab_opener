# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [Unreleased]

### Added
- Korean, Traditional Chinese, Simplified Chinese README files with 5-language cross-links
- Vertical scrollbar for TabView tab list (3-row visible area, unlimited rows)
- Tk 9.0 `<TouchpadScroll>` event support for macOS trackpad scrolling
- Thread exception notification via error dialog (previously silent)
- Debug logging for scroll and mousewheel diagnostics

### Changed
- **gui.py split into modules**: `main_window.py`, `widgets.py`, `tab_group.py`, `history.py` for maintainability
- TabView layout: auto-wrap buttons with scrollable area (replaces fixed 4-row limit)
- Tab group copy naming: base name extraction convention (`"Work"` → `"Work 1"` → `"Work 2"`)
- Tab deletion now selects right neighbor (or left if rightmost)
- Auto-scroll driven by `<Configure>` event instead of timer
- CJK-aware tab button width estimation using `unicodedata.east_asian_width()`
- Language switcher uses index-based lookup instead of name-based reverse search
- Dynamic version resolution via `importlib.metadata` (removes hardcoded fallback)
- AppleScript helpers extracted to eliminate code duplication in `opener_mac.py`
- Backward-compat re-exports in `gui.py` cleaned up
- Test count: 116 passed, 1 skipped (was 68)

### Fixed
- `_opening` flag double-reset race condition between timer and thread completion
- `TclError` in history dropdown FocusOut when widget already destroyed
- `normpath` mismatch in pin toggle (expanduser-only value passed to normpath comparison)
- TabView buttons not rendering after layout change
- TabView text clipping and selection color contrast
- Mousewheel scroll not working in TabView (switched to `bind_all`)
- `scroll_to_current` positioning accuracy (`winfo_y()` based)
- Dead test `test_foreground_is_explorer` (was ending with `pass`)

## [1.0.0] - 2026-02-15

### Added
- Tab group management (create, rename, delete, reorder)
- Tab group copy (duplicate with auto-incremented name)
- One-click open: open all folders in a group as Explorer/Finder tabs
- History with pin: track recently opened folders, pin favorites
- Cross-platform support: Windows (Explorer tabs, Win 11+) and macOS (Finder tabs)
- Dual theme: customtkinter for modern UI, fallback to standard tkinter
- i18n: English, Japanese, Korean, Traditional Chinese, Simplified Chinese
- Language switcher and timeout selector in settings
- Path list with horizontal scroll
- Geometry input (window position/size) with auto-save on tab switch
- "Get from Explorer/Finder" button to capture current window geometry
- Default "Tab 1" tab on first launch
- Log rotation (1 MB max, 3 backups)
- Address bar input verification with retry (Windows pywinauto UIA)
- Three-tier fallback for Windows: pywinauto UIA → ctypes SendInput → separate windows
- Two-tier fallback for macOS: AppleScript + System Events → separate windows
- PyInstaller build support (.spec file included)

### Technical
- Installable Python package with pyproject.toml (Hatchling build system)
- 68 tests (40 config + 28 i18n)
