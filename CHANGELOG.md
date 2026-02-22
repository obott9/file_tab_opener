# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

## [1.1.1] - 2026-02-23

### Added
- Toast notification overlay during tab opening ("Opening tabs... Please wait.")
- Toast follows OS dark/light theme via `customtkinter.get_appearance_mode()`
- Windows `.ico` icon for PyInstaller builds (generated from source PNG with flood-fill transparency)
- Comprehensive logging across config.py, main_window.py, history.py, tab_group.py, widgets.py

### Changed
- Icon files (`.ico`, `.icns`) moved to `assets/` (git-ignored); spec file paths updated
- AppleScript escape hardening: newline characters (`\n`, `\r`) now stripped in `opener_mac.py`
- Empty/whitespace-only tab group names are now rejected in `config.add_tab_group()`

### Fixed
- `widgets.scroll_to_current()`: bare `except Exception: pass` replaced with `log.debug`

## [1.1.0] - 2026-02-22

### Added
- Korean, Traditional Chinese, Simplified Chinese README files with 5-language cross-links
- Vertical scrollbar for TabView tab list (3-row visible area, unlimited rows)
- Tk 9.0 `<TouchpadScroll>` event support for macOS trackpad scrolling
- Thread exception notification via error dialog (previously silent)
- Debug logging for scroll and mousewheel diagnostics
- PyInstaller `.spec` file with proper macOS metadata (bundle ID, version, plist)
- GitHub Actions CI/CD workflow for cross-platform testing (Ubuntu, macOS, Windows × Python 3.10–3.13)
- Custom app icon (`FileTabOpener.icns`)

### Changed
- **macOS config path**: moved from `~/.file_tab_opener.json` to `~/Library/Application Support/FileTabOpener/config.json` (macOS standard)
- **gui.py split into modules**: `main_window.py`, `widgets.py`, `tab_group.py`, `history.py` for maintainability
- TabView layout: auto-wrap buttons with scrollable area (replaces fixed 4-row limit)
- Tab group copy naming: base name extraction convention (`"Work"` → `"Work 1"` → `"Work 2"`)
- Tab deletion now selects right neighbor (or left if rightmost)
- Auto-scroll driven by `<Configure>` event instead of timer
- CJK-aware tab button width estimation using `unicodedata.east_asian_width()`
- Language switcher uses index-based lookup instead of name-based reverse search
- Dynamic version resolution via `importlib.metadata` (removes hardcoded fallback)
- **AppleScript tab opening**: replaced fixed delays with retry-based completion detection (adapts to Mac speed)
- AppleScript helpers extracted to eliminate code duplication in `opener_mac.py`
- `validate_paths` extracted to `__init__.py` (shared by `opener_mac` and `opener_win`)
- `widgets.py` now defines `__all__` to control wildcard exports
- `TabGroupSection.restore_tab_state()` public API (replaces private method calls from MainWindow)
- Backward-compat re-exports in `gui.py` cleaned up
- Test count: 127 passed (was 68)

### Fixed
- Duplicate paths now deduplicated before opening tabs (prevented tab target corruption)
- AppleScript tab creation: wait for window id change after ⌘T before `set target` (fixes tabs pointing to wrong directories)
- `TclError` crash when window closed during tab-opening thread (`root.after` in worker)
- History dropdown selection now strips display prefix (📌/spaces) before inserting into entry
- Placeholder detection uses flag instead of fragile string comparison
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
