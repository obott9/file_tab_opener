# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/).

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
