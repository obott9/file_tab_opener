"""
File Tab Opener -- A GUI tool for opening multiple folders as tabs
in macOS Finder or Windows Explorer.

Entry point. Supports both `python -m file_tab_opener` and console_scripts.
"""

from __future__ import annotations

import logging
import logging.handlers
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
        file_handler = logging.handlers.RotatingFileHandler(
            log_path, encoding="utf-8", maxBytes=1_000_000, backupCount=3,
        )
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
        from file_tab_opener import opener_win as opener
        return opener
    elif system == "Darwin":
        from file_tab_opener import opener_mac as opener
        return opener
    else:
        print(f"Unsupported platform: {system}", file=sys.stderr)
        sys.exit(1)


def main() -> None:
    """Application entry point."""
    _setup_logging()
    log = logging.getLogger(__name__)

    # Load configuration
    from file_tab_opener.config import ConfigManager

    config = ConfigManager()
    config.load()
    log.info("Config loaded: %s", config.path)

    # Initialize i18n: use saved language, otherwise detect from system
    from file_tab_opener import i18n
    saved_lang = config.data.settings.get("language")
    if saved_lang and isinstance(saved_lang, str):
        i18n.set_language(saved_lang)
    else:
        i18n.init()
    log.info("Language: %s", i18n.get_language())

    # Import platform-specific opener
    opener = _get_opener()
    log.info("Platform: %s, opener: %s", platform.system(), opener.__name__)

    # Build and run GUI
    from file_tab_opener.main_window import MainWindow

    app = MainWindow(config, opener)
    app.build()
    app.run()


if __name__ == "__main__":
    main()
