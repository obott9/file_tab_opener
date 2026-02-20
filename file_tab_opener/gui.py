"""
GUI module for File Tab Opener.

This module re-exports all public names from the split sub-modules
for backward compatibility.
"""

from file_tab_opener.widgets import *  # noqa: F401, F403
from file_tab_opener.widgets import _strip_quotes, _setup_placeholder  # noqa: F401
from file_tab_opener.history import HistorySection  # noqa: F401
from file_tab_opener.tab_group import TabGroupSection, MIN_WINDOW_WIDTH, MIN_WINDOW_HEIGHT  # noqa: F401
from file_tab_opener.main_window import MainWindow  # noqa: F401

# Backward compatibility aliases
FINDER_MIN_WIDTH = MIN_WINDOW_WIDTH
FINDER_MIN_HEIGHT = MIN_WINDOW_HEIGHT
