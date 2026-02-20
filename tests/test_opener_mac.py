"""Tests for opener_mac module.

Covers: validate_paths (with mocked Path.is_dir), _build_applescript.
"""

from __future__ import annotations

from unittest.mock import patch

import pytest

from file_tab_opener.opener_mac import validate_paths, _build_applescript


# ============================================================
# validate_paths
# ============================================================


class TestValidatePaths:
    """Test validate_paths with mocked filesystem."""

    @patch("file_tab_opener.opener_mac.Path.is_dir")
    def test_all_valid(self, mock_is_dir) -> None:
        mock_is_dir.return_value = True
        valid, invalid = validate_paths(["/Users/test/Documents", "/Users/test/Downloads"])
        assert len(valid) == 2
        assert len(invalid) == 0

    @patch("file_tab_opener.opener_mac.Path.is_dir")
    def test_all_invalid(self, mock_is_dir) -> None:
        mock_is_dir.return_value = False
        valid, invalid = validate_paths(["/nonexistent/a", "/nonexistent/b"])
        assert len(valid) == 0
        assert len(invalid) == 2

    @patch("file_tab_opener.opener_mac.Path.is_dir")
    def test_mixed(self, mock_is_dir) -> None:
        mock_is_dir.side_effect = [True, False, True]
        valid, invalid = validate_paths(["/good/a", "/bad/b", "/good/c"])
        assert len(valid) == 2
        assert len(invalid) == 1
        assert invalid[0] == "/bad/b"

    def test_empty_list(self) -> None:
        valid, invalid = validate_paths([])
        assert valid == []
        assert invalid == []

    @patch("file_tab_opener.opener_mac.Path.is_dir")
    def test_expanduser(self, mock_is_dir) -> None:
        """Paths with ~ should be expanded."""
        mock_is_dir.return_value = True
        valid, invalid = validate_paths(["~/Documents"])
        assert len(valid) == 1
        assert "~" not in valid[0]


# ============================================================
# _build_applescript
# ============================================================


class TestBuildAppleScript:
    """Test AppleScript generation."""

    def test_single_path(self) -> None:
        script = _build_applescript(["/Users/test/Documents"])
        assert 'tell application "Finder"' in script
        assert 'make new Finder window' in script
        assert "/Users/test/Documents" in script
        # No System Events for single path
        assert 'tell application "System Events"' not in script

    def test_multiple_paths(self) -> None:
        script = _build_applescript(["/path/a", "/path/b", "/path/c"])
        assert 'tell application "Finder"' in script
        assert 'tell application "System Events"' in script
        assert 'keystroke "t" using command down' in script
        assert "/path/a" in script
        assert "/path/b" in script
        assert "/path/c" in script

    def test_with_window_rect(self) -> None:
        script = _build_applescript(["/path/a"], window_rect=(100, 200, 800, 600))
        assert "set bounds of front Finder window to {100, 200, 900, 800}" in script

    def test_escape_quotes_in_path(self) -> None:
        script = _build_applescript(['/path/with"quote'])
        assert r'\"' in script

    def test_escape_backslash_in_path(self) -> None:
        script = _build_applescript(["/path/with\\backslash"])
        assert "\\\\" in script

    def test_two_paths_has_one_system_events(self) -> None:
        script = _build_applescript(["/a", "/b"])
        count = script.count('tell application "System Events"')
        assert count == 1

    def test_three_paths_has_two_system_events(self) -> None:
        script = _build_applescript(["/a", "/b", "/c"])
        count = script.count('tell application "System Events"')
        assert count == 2
