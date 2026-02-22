"""Tests for opener_mac module.

Covers: validate_paths (with mocked Path.is_dir), _build_applescript,
open_single_folder, open_folders_as_tabs, _esc_applescript.
"""

from __future__ import annotations

from unittest.mock import patch, MagicMock

import pytest

from file_tab_opener.opener_mac import (
    validate_paths,
    _build_applescript,
    _esc_applescript,
    open_single_folder,
    open_folders_as_tabs,
)


# ============================================================
# validate_paths
# ============================================================


class TestValidatePaths:
    """Test validate_paths with mocked filesystem."""

    @patch("file_tab_opener.Path.is_dir")
    def test_all_valid(self, mock_is_dir) -> None:
        mock_is_dir.return_value = True
        valid, invalid = validate_paths(["/Users/test/Documents", "/Users/test/Downloads"])
        assert len(valid) == 2
        assert len(invalid) == 0

    @patch("file_tab_opener.Path.is_dir")
    def test_all_invalid(self, mock_is_dir) -> None:
        mock_is_dir.return_value = False
        valid, invalid = validate_paths(["/nonexistent/a", "/nonexistent/b"])
        assert len(valid) == 0
        assert len(invalid) == 2

    @patch("file_tab_opener.Path.is_dir")
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

    @patch("file_tab_opener.Path.is_dir")
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

    def test_retry_loop_for_tabs(self) -> None:
        """Each additional tab waits for window id change before set target."""
        script = _build_applescript(["/a", "/b"])
        assert "repeat" in script
        assert "exit repeat" in script
        assert "set prevId to id of front Finder window" in script
        assert "if curId is not prevId then exit repeat" in script
        # No fixed delay between keystroke and set target
        assert "delay 0.5" not in script
        assert "delay 0.3" not in script

    def test_single_path_no_retry(self) -> None:
        """Single path should not have retry loop."""
        script = _build_applescript(["/a"])
        assert "repeat" not in script

    def test_retry_count_matches_constant(self) -> None:
        """Retry count in generated script matches _RETRY_MAX."""
        from file_tab_opener.opener_mac import _RETRY_MAX
        script = _build_applescript(["/a", "/b"])
        assert f"repeat {_RETRY_MAX} times" in script


# ============================================================
# _esc_applescript
# ============================================================


class TestEscAppleScript:
    """Test AppleScript string escaping."""

    def test_escape_backslash(self) -> None:
        assert _esc_applescript("a\\b") == "a\\\\b"

    def test_escape_double_quote(self) -> None:
        assert _esc_applescript('a"b') == 'a\\"b'

    def test_strip_newlines(self) -> None:
        assert _esc_applescript("line1\nline2\rline3") == "line1line2line3"

    def test_no_special_chars(self) -> None:
        assert _esc_applescript("/Users/test/Documents") == "/Users/test/Documents"

    def test_combined(self) -> None:
        result = _esc_applescript('path\\with"quote\n')
        assert "\n" not in result
        assert '\\"' in result
        assert "\\\\" in result


# ============================================================
# open_single_folder
# ============================================================


class TestOpenSingleFolder:
    """Test open_single_folder with mocked subprocess."""

    @patch("file_tab_opener.opener_mac.subprocess.run")
    def test_success(self, mock_run: MagicMock) -> None:
        """Should return True on success."""
        mock_run.return_value = MagicMock(returncode=0)
        result = open_single_folder("/Users/test/Documents")
        assert result is True
        mock_run.assert_called_once()

    @patch("file_tab_opener.opener_mac.subprocess.run")
    def test_with_window_rect(self, mock_run: MagicMock) -> None:
        """Should pass window_rect to AppleScript."""
        mock_run.return_value = MagicMock(returncode=0)
        result = open_single_folder("/test", window_rect=(10, 20, 800, 600))
        assert result is True
        # Verify the script includes bounds
        call_args = mock_run.call_args
        script = call_args[0][0][2]  # ["osascript", "-e", script]
        assert "set bounds" in script

    @patch("file_tab_opener.opener_mac.subprocess.run", side_effect=OSError("fail"))
    def test_os_error(self, mock_run: MagicMock) -> None:
        """Should return False on OSError."""
        result = open_single_folder("/test")
        assert result is False

    @patch("file_tab_opener.opener_mac.subprocess.run", side_effect=__import__("subprocess").TimeoutExpired("cmd", 30))
    def test_timeout(self, mock_run: MagicMock) -> None:
        """Should return False on timeout."""
        result = open_single_folder("/test", timeout=1.0)
        assert result is False


# ============================================================
# open_folders_as_tabs
# ============================================================


class TestOpenFoldersAsTabs:
    """Test open_folders_as_tabs with mocked subprocess."""

    @patch("file_tab_opener.opener_mac._run_applescript")
    def test_success(self, mock_run: MagicMock) -> None:
        """Should return True when AppleScript succeeds."""
        mock_run.return_value = (True, "")
        result = open_folders_as_tabs(["/a", "/b"])
        assert result is True

    @patch("file_tab_opener.opener_mac._open_separate")
    @patch("file_tab_opener.opener_mac._run_applescript")
    def test_fallback_on_failure(self, mock_run: MagicMock, mock_separate: MagicMock) -> None:
        """Should fall back to _open_separate on AppleScript failure."""
        mock_run.return_value = (False, "some error")
        mock_separate.return_value = True
        result = open_folders_as_tabs(["/a", "/b"])
        assert result is True
        mock_separate.assert_called_once()

    def test_empty_paths(self) -> None:
        """Should return False for empty paths."""
        result = open_folders_as_tabs([])
        assert result is False

    @patch("file_tab_opener.opener_mac._run_applescript")
    def test_deduplicates_paths(self, mock_run: MagicMock) -> None:
        """Should deduplicate paths before opening."""
        mock_run.return_value = (True, "")
        open_folders_as_tabs(["/a", "/b", "/a"])
        # Verify script only has /a once (via the call to _run_applescript)
        call_args = mock_run.call_args
        script = call_args[0][0]
        # Count occurrences of "/a" in the script
        assert script.count('"/a"') == 1

    @patch("file_tab_opener.opener_mac._run_applescript")
    def test_on_error_callback(self, mock_run: MagicMock) -> None:
        """Should call on_error when AppleScript fails."""
        mock_run.return_value = (False, "test error")
        errors: list[tuple[str, str]] = []
        with patch("file_tab_opener.opener_mac._open_separate", return_value=True):
            open_folders_as_tabs(
                ["/a"],
                on_error=lambda p, e: errors.append((p, e)),
            )
        assert len(errors) == 1
        assert "test error" in errors[0][1]

    @patch("file_tab_opener.opener_mac._run_applescript")
    def test_accessibility_error(self, mock_run: MagicMock) -> None:
        """Should show accessibility message on permission errors."""
        mock_run.return_value = (False, "assistive access required")
        errors: list[tuple[str, str]] = []
        with patch("file_tab_opener.opener_mac._open_separate", return_value=True):
            open_folders_as_tabs(
                ["/a"],
                on_error=lambda p, e: errors.append((p, e)),
            )
        assert len(errors) == 1
        # Should use the i18n accessibility message, not raw error
        assert "assistive" not in errors[0][1].lower() or "accessibility" in errors[0][1].lower()
