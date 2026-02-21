"""Tests for opener_win module.

Covers: validate_paths, get_frontmost_explorer_rect(), _is_explorer_hwnd(),
_enum_explorer_hwnds() — all with mocked ctypes calls.
"""

from __future__ import annotations

import sys
from unittest.mock import MagicMock, patch

import pytest

# Skip entire module on non-Windows platforms (both collection and execution)
if sys.platform != "win32":
    pytest.skip("Windows-only tests", allow_module_level=True)

import ctypes
import ctypes.wintypes as wintypes

from file_tab_opener.opener_win import (
    get_frontmost_explorer_rect,
    validate_paths,
    _is_explorer_hwnd,
    _enum_explorer_hwnds,
)


# ============================================================
# validate_paths
# ============================================================


class TestValidatePaths:
    """Test validate_paths with mocked filesystem."""

    @patch("file_tab_opener.Path.is_dir")
    def test_all_valid(self, mock_is_dir: MagicMock) -> None:
        mock_is_dir.return_value = True
        valid, invalid = validate_paths([r"C:\Users\test\Documents"])
        assert len(valid) == 1
        assert len(invalid) == 0

    @patch("file_tab_opener.Path.is_dir")
    def test_expanduser(self, mock_is_dir: MagicMock) -> None:
        """Paths with ~ should be expanded."""
        mock_is_dir.return_value = True
        valid, invalid = validate_paths(["~/Documents"])
        assert len(valid) == 1
        assert "~" not in valid[0]


# ============================================================
# _is_explorer_hwnd
# ============================================================


class TestIsExplorerHwnd:
    """Tests for _is_explorer_hwnd()."""

    @patch("file_tab_opener.opener_win.ctypes")
    def test_returns_true_for_cabinet_class(self, mock_ctypes: MagicMock) -> None:
        """Return True when the window class is CabinetWClass."""
        buf = ctypes.create_unicode_buffer(256)
        buf.value = "CabinetWClass"
        mock_ctypes.create_unicode_buffer.return_value = buf
        mock_ctypes.windll.user32.GetClassNameW.return_value = 15

        assert _is_explorer_hwnd(12345) is True

    @patch("file_tab_opener.opener_win.ctypes")
    def test_returns_false_for_other_class(self, mock_ctypes: MagicMock) -> None:
        """Return False when the window class is not CabinetWClass."""
        buf = ctypes.create_unicode_buffer(256)
        buf.value = "Notepad"
        mock_ctypes.create_unicode_buffer.return_value = buf
        mock_ctypes.windll.user32.GetClassNameW.return_value = 7

        assert _is_explorer_hwnd(12345) is False


# ============================================================
# get_frontmost_explorer_rect
# ============================================================


class TestGetFrontmostExplorerRect:
    """Tests for get_frontmost_explorer_rect()."""

    @patch("file_tab_opener.opener_win._enum_explorer_hwnds")
    @patch("file_tab_opener.opener_win._is_explorer_hwnd")
    @patch("file_tab_opener.opener_win.wintypes")
    @patch("file_tab_opener.opener_win.ctypes")
    def test_foreground_is_explorer(
        self,
        mock_ctypes: MagicMock,
        mock_wintypes: MagicMock,
        mock_is_explorer: MagicMock,
        mock_enum: MagicMock,
    ) -> None:
        """Use the foreground window when it is an Explorer window."""
        mock_ctypes.windll.user32.GetForegroundWindow.return_value = 100
        mock_is_explorer.return_value = True

        mock_rect = MagicMock()
        mock_rect.left = 50
        mock_rect.top = 100
        mock_rect.right = 850
        mock_rect.bottom = 700
        mock_wintypes.RECT.return_value = mock_rect

        mock_ctypes.windll.user32.GetWindowRect.return_value = True
        mock_ctypes.byref.return_value = MagicMock()

        result = get_frontmost_explorer_rect()

        assert result == (50, 100, 800, 600)
        mock_ctypes.windll.user32.GetWindowRect.assert_called_once()

    @patch("file_tab_opener.opener_win._enum_explorer_hwnds")
    @patch("file_tab_opener.opener_win._is_explorer_hwnd")
    def test_no_explorer_windows(
        self,
        mock_is_explorer: MagicMock,
        mock_enum: MagicMock,
    ) -> None:
        """Return None when no Explorer window exists."""
        mock_is_explorer.return_value = False
        mock_enum.return_value = []

        with patch("file_tab_opener.opener_win.ctypes") as mock_ctypes:
            mock_ctypes.windll.user32.GetForegroundWindow.return_value = 999
            result = get_frontmost_explorer_rect()

        assert result is None

    @patch("file_tab_opener.opener_win._enum_explorer_hwnds")
    @patch("file_tab_opener.opener_win._is_explorer_hwnd")
    @patch("file_tab_opener.opener_win.wintypes")
    @patch("file_tab_opener.opener_win.ctypes")
    def test_fallback_to_enum(
        self,
        mock_ctypes: MagicMock,
        mock_wintypes: MagicMock,
        mock_is_explorer: MagicMock,
        mock_enum: MagicMock,
    ) -> None:
        """Fall back to _enum_explorer_hwnds when foreground is not Explorer."""
        mock_ctypes.windll.user32.GetForegroundWindow.return_value = 999
        mock_is_explorer.return_value = False
        mock_enum.return_value = [200, 300]

        mock_rect = MagicMock()
        mock_rect.left = 10
        mock_rect.top = 20
        mock_rect.right = 810
        mock_rect.bottom = 620
        mock_wintypes.RECT.return_value = mock_rect

        mock_ctypes.windll.user32.GetWindowRect.return_value = True
        mock_ctypes.byref.return_value = MagicMock()

        result = get_frontmost_explorer_rect()

        assert result == (10, 20, 800, 600)
        mock_ctypes.windll.user32.GetWindowRect.assert_called_once()

    @patch("file_tab_opener.opener_win._enum_explorer_hwnds")
    @patch("file_tab_opener.opener_win._is_explorer_hwnd")
    @patch("file_tab_opener.opener_win.wintypes")
    @patch("file_tab_opener.opener_win.ctypes")
    def test_get_window_rect_failure(
        self,
        mock_ctypes: MagicMock,
        mock_wintypes: MagicMock,
        mock_is_explorer: MagicMock,
        mock_enum: MagicMock,
    ) -> None:
        """Return None when GetWindowRect fails."""
        mock_ctypes.windll.user32.GetForegroundWindow.return_value = 100
        mock_is_explorer.return_value = True

        mock_rect = MagicMock()
        mock_wintypes.RECT.return_value = mock_rect

        mock_ctypes.windll.user32.GetWindowRect.return_value = False
        mock_ctypes.byref.return_value = MagicMock()

        result = get_frontmost_explorer_rect()

        assert result is None
