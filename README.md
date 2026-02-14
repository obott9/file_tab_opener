# File Tab Opener

[日本語版 README はこちら](README_ja.md)

A GUI tool for opening multiple folders as tabs in a single **Windows Explorer** or **macOS Finder** window.

Instead of opening folders one by one, register them in a named tab group and open them all at once — each folder appears as a separate tab in the same window.

## Features

- **Tab Group Management** — Create named groups (e.g. "Work", "Personal") and assign folder paths to each
- **One-Click Open** — Open all folders in a group as tabs in a single Explorer/Finder window
- **History with Pin** — Recently opened folders are tracked; pin frequently used ones
- **Cross-Platform** — Windows (Explorer tabs, Win 11+) and macOS (Finder tabs)
- **Dual Theme** — Uses [customtkinter](https://github.com/TomSchimansky/CustomTkinter) for a modern look; falls back to standard tkinter if unavailable
- **i18n** — English, Japanese, Korean, Traditional Chinese, Simplified Chinese (auto-detected from system locale)

## Requirements

- Python 3.10+
- Windows 11+ or macOS 12+

## Installation

```bash
git clone https://github.com/obott9/file_tab_opener.git
cd file_tab_opener
pip install .
```

With all optional dependencies (recommended):

```bash
pip install .[all]
```

### Optional Dependencies

| Package | Purpose | Install |
|---------|---------|---------|
| customtkinter | Modern themed GUI | `pip install .[ui]` |
| pywinauto | Reliable Explorer tab automation (Windows) | `pip install .[windows]` |

## Usage

```bash
file-tab-opener
```

Or run as a Python module:

```bash
python -m file_tab_opener
```

### Quick Start

1. Launch the app
2. Click **+ Add Tab** to create a tab group (e.g. "Project A")
3. Add folder paths using the text field, **Browse** button, or paste from Explorer
4. Click **Open as Tabs** to open all folders as tabs in one window

### History Section

- Type or paste a folder path into the combobox and click **Open** to open it
- The path is automatically saved to history
- Click **Pin** to keep a path at the top of the list
- Click **Clear** to remove all unpinned history entries

## How It Works

### Windows (Explorer Tabs)

Three-tier fallback for maximum compatibility:

1. **pywinauto UIA** — Opens a new Explorer window, connects via UI Automation, sends Ctrl+T for new tabs, and sets the address bar text via UIA ValuePattern. Most reliable method.
2. **ctypes SendInput** — Same keystroke approach using raw Win32 `SendInput` API. No external dependencies, but less reliable due to focus and timing issues.
3. **Separate windows** — Falls back to opening each folder in its own Explorer window via `subprocess`.

### macOS (Finder Tabs)

Two-tier fallback:

1. **AppleScript + System Events** — Opens the first folder in Finder, then sends ⌘T keystrokes to create new tabs and sets each tab's target via AppleScript.
2. **Separate windows** — Falls back to `open` command for individual windows.

> **Note:** The AppleScript method requires Accessibility permission. Go to **System Settings → Privacy & Security → Accessibility** and enable access for Terminal.app (or your terminal emulator).

### Performance Note (Windows)

Windows Explorer does not provide a public API for tab operations. All methods rely on UI Automation or keystroke simulation (`Ctrl+T` → address bar input), which requires `delay` waits between each tab for the UI to respond. Opening many tabs will be noticeably slower than on macOS, where Finder supports direct tab manipulation via AppleScript.

## Configuration

Settings are stored in a JSON file:

| OS | Path |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\config.json` |
| macOS | `~/.file_tab_opener.json` |
| Linux | `~/.config/file_tab_opener/config.json` |

## Logging

The app outputs status messages to the terminal (`INFO` level) and writes detailed logs to a file (`DEBUG` level).

| Output | Level | Purpose |
|--------|-------|---------|
| Terminal (stderr) | INFO+ | Startup progress, operation results |
| Log file | DEBUG+ | Detailed diagnostics for troubleshooting |

Log file location:

| OS | Path |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\debug.log` |
| macOS | `~/Library/Logs/FileTabOpener/debug.log` |
| Linux | `~/.local/share/FileTabOpener/debug.log` |

## Development

```bash
# Install with dev dependencies (editable mode)
pip install -e .[all,dev]

# Run tests
pytest tests/ -v
```

## Build Standalone App

You can build a standalone `.app` (macOS) or `.exe` (Windows) using [PyInstaller](https://pyinstaller.org/). No code signing is needed for personal use.

```bash
# Install PyInstaller
pip install pyinstaller

# Build (run on the OS you want to build for)
pyinstaller --noconfirm --onedir --windowed \
    --collect-all customtkinter \
    --name "File Tab Opener" \
    file_tab_opener/__main__.py
```

The output is in `dist/File Tab Opener/`. On macOS, a `.app` bundle is created; on Windows, a `.exe` folder.

> **Note:** You must build on each OS separately — a macOS build cannot produce a Windows `.exe`, and vice versa.

## Project Structure

```
file_tab_opener/
├── pyproject.toml           # Package configuration
├── LICENSE                  # MIT License
├── README.md                # This file
├── README_ja.md             # Japanese README
├── file_tab_opener/         # Source package
│   ├── __init__.py
│   ├── __main__.py          # Entry point
│   ├── config.py            # Configuration management
│   ├── i18n.py              # Internationalization (5 languages)
│   ├── gui.py               # GUI (customtkinter / tkinter)
│   ├── opener_win.py        # Windows Explorer tab opener
│   └── opener_mac.py        # macOS Finder tab opener
└── tests/
    ├── test_config.py       # Config module tests (40 tests)
    └── test_i18n.py         # i18n module tests (28 tests)
```

## License

[MIT License](LICENSE) © 2026 obott9
