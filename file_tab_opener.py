"""
File Tab Opener -- A GUI tool for opening multiple folders as tabs
in macOS Finder or Windows Explorer.

Entry point.
"""

from __future__ import annotations

import logging
import os
import platform
import sys
from types import ModuleType


def _setup_logging() -> None:
    """Configure logging with console and file handlers."""
    log_fmt = "%(asctime)s [%(levelname)s] %(name)s: %(message)s"
    date_fmt = "%H:%M:%S"

    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # Console output (INFO and above)
    console = logging.StreamHandler()
    console.setLevel(logging.INFO)
    console.setFormatter(logging.Formatter(log_fmt, datefmt=date_fmt))
    root_logger.addHandler(console)

    # File output (DEBUG and above)
    try:
        system = platform.system()
        if system == "Windows":
            log_dir = os.path.join(
                os.environ.get("APPDATA", os.path.expanduser("~")),
                "FileTabOpener",
            )
        elif system == "Darwin":
            log_dir = os.path.join(os.path.expanduser("~"), "Library", "Logs", "FileTabOpener")
        else:
            log_dir = os.path.join(os.path.expanduser("~"), ".local", "share", "FileTabOpener")

        os.makedirs(log_dir, exist_ok=True)
        log_path = os.path.join(log_dir, "debug.log")
        file_handler = logging.FileHandler(log_path, encoding="utf-8", mode="w")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(logging.Formatter(log_fmt, datefmt=date_fmt))
        root_logger.addHandler(file_handler)
        logging.getLogger(__name__).info("Log file: %s", log_path)
    except Exception as e:
        logging.getLogger(__name__).warning("Failed to create log file: %s", e)


def _get_opener() -> ModuleType:
    """Import and return the platform-specific opener module."""
    system = platform.system()
    if system == "Windows":
        import opener_win as opener
        return opener
    elif system == "Darwin":
        import opener_mac as opener
        return opener
    else:
        print(f"Unsupported platform: {system}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Application entry point."""
    _setup_logging()
    log = logging.getLogger(__name__)

    # Initialize i18n (must be before GUI construction)
    import i18n
    i18n.init()
    log.info("Language: %s", i18n.get_language())

    # Load configuration
    from config import ConfigManager

    config = ConfigManager()
    config.load()
    log.info("Config loaded: %s", config.path)

    # Import platform-specific opener
    opener = _get_opener()
    log.info("Platform: %s, opener: %s", platform.system(), opener.__name__)

    # Build and run GUI
    from gui import MainWindow

    app = MainWindow(config, opener)
    app.build()
    app.run()


if __name__ == "__main__":
    main()
