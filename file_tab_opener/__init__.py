"""File Tab Opener -- Open multiple folders as tabs in Explorer/Finder."""

try:
    from importlib.metadata import version

    __version__ = version("file-tab-opener")
except Exception:
    __version__ = "1.0.0"
