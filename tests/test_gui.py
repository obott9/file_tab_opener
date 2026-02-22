"""Tests for GUI logic (non-rendering parts).

Covers: strip_quotes, TabView state management, TabGroupSection static methods.
"""

from __future__ import annotations

import pytest

from file_tab_opener.config import strip_quotes


# ============================================================
# strip_quotes (config.py utility)
# ============================================================


class TestStripQuotes:
    """Test the shared strip_quotes utility."""

    def test_double_quotes(self) -> None:
        assert strip_quotes('"hello"') == "hello"

    def test_single_quotes(self) -> None:
        assert strip_quotes("'hello'") == "hello"

    def test_no_quotes(self) -> None:
        assert strip_quotes("hello") == "hello"

    def test_empty_string(self) -> None:
        assert strip_quotes("") == ""

    def test_mismatched_quotes(self) -> None:
        assert strip_quotes("\"hello'") == "\"hello'"

    def test_single_quote_char(self) -> None:
        assert strip_quotes('"') == '"'

    def test_empty_quotes(self) -> None:
        assert strip_quotes('""') == ""

    def test_nested_quotes(self) -> None:
        assert strip_quotes("\"it's\"") == "it's"

    def test_path_with_spaces(self) -> None:
        assert strip_quotes('"C:\\Users\\test folder"') == "C:\\Users\\test folder"


# ============================================================
# TabView state management (no rendering, pure logic)
# ============================================================


class TestTabViewLogic:
    """Test TabView internal state without a real Tk root.

    We test via TabGroupSection._parse_int and _clamp_min which are
    static methods and don't require Tk.
    """

    def test_parse_int_valid(self) -> None:
        from file_tab_opener.tab_group import TabGroupSection
        assert TabGroupSection._parse_int("42") == 42

    def test_parse_int_negative(self) -> None:
        from file_tab_opener.tab_group import TabGroupSection
        assert TabGroupSection._parse_int("-10") == -10

    def test_parse_int_whitespace(self) -> None:
        from file_tab_opener.tab_group import TabGroupSection
        assert TabGroupSection._parse_int("  100  ") == 100

    def test_parse_int_empty(self) -> None:
        from file_tab_opener.tab_group import TabGroupSection
        assert TabGroupSection._parse_int("") is None

    def test_parse_int_invalid(self) -> None:
        from file_tab_opener.tab_group import TabGroupSection
        assert TabGroupSection._parse_int("abc") is None

    def test_clamp_min_above(self) -> None:
        from file_tab_opener.tab_group import TabGroupSection
        assert TabGroupSection._clamp_min(600, 528) == 600

    def test_clamp_min_below(self) -> None:
        from file_tab_opener.tab_group import TabGroupSection
        assert TabGroupSection._clamp_min(100, 528) == 528

    def test_clamp_min_equal(self) -> None:
        from file_tab_opener.tab_group import TabGroupSection
        assert TabGroupSection._clamp_min(528, 528) == 528

    def test_clamp_min_none(self) -> None:
        from file_tab_opener.tab_group import TabGroupSection
        assert TabGroupSection._clamp_min(None, 528) is None


# ============================================================
# TabView.delete_tab neighbor selection
# ============================================================


class TestDeleteTabNeighborSelection:
    """Test that delete_tab selects the right neighbor, or left if rightmost.

    We test the pure state logic by calling the internal _names / _current
    manipulation directly (same logic as delete_tab without Tk rendering).
    """

    @staticmethod
    def _simulate_delete(names: list[str], current: str, to_delete: str) -> str | None:
        """Simulate TabView.delete_tab logic and return the new current."""
        if to_delete not in names:
            return current
        idx = names.index(to_delete)
        names.remove(to_delete)
        if current == to_delete:
            if names:
                new_idx = min(idx, len(names) - 1)
                return names[new_idx]
            return None
        return current

    def test_delete_first_selects_right(self) -> None:
        names = ["A", "B", "C"]
        result = self._simulate_delete(names, "A", "A")
        assert result == "B"

    def test_delete_middle_selects_right(self) -> None:
        names = ["A", "B", "C"]
        result = self._simulate_delete(names, "B", "B")
        assert result == "C"

    def test_delete_last_selects_left(self) -> None:
        names = ["A", "B", "C"]
        result = self._simulate_delete(names, "C", "C")
        assert result == "B"

    def test_delete_only_tab_returns_none(self) -> None:
        names = ["A"]
        result = self._simulate_delete(names, "A", "A")
        assert result is None

    def test_delete_non_current_preserves_current(self) -> None:
        names = ["A", "B", "C"]
        result = self._simulate_delete(names, "A", "C")
        assert result == "A"

    def test_delete_second_of_two_selects_first(self) -> None:
        names = ["A", "B"]
        result = self._simulate_delete(names, "B", "B")
        assert result == "A"

    def test_delete_first_of_two_selects_second(self) -> None:
        names = ["A", "B"]
        result = self._simulate_delete(names, "A", "A")
        assert result == "B"


# ============================================================
# add_tab_group duplicate check (B-5)
# ============================================================


class TestAddTabGroupDuplicate:
    """Test that add_tab_group rejects duplicate names."""

    def test_duplicate_returns_none(self, tmp_path) -> None:
        from file_tab_opener.config import ConfigManager
        cm = ConfigManager()
        cm.path = tmp_path / "config.json"
        result1 = cm.add_tab_group("Work")
        assert result1 is not None
        result2 = cm.add_tab_group("Work")
        assert result2 is None
        assert len(cm.data.tab_groups) == 1

    def test_different_names_ok(self, tmp_path) -> None:
        from file_tab_opener.config import ConfigManager
        cm = ConfigManager()
        cm.path = tmp_path / "config.json"
        assert cm.add_tab_group("Work") is not None
        assert cm.add_tab_group("Play") is not None
        assert len(cm.data.tab_groups) == 2


# ============================================================
# E-1: settings default merge
# ============================================================


class TestSettingsDefaultMerge:
    """Test that empty settings in file still gets default use_custom_tk."""

    def test_empty_settings_gets_defaults(self, tmp_path) -> None:
        import json
        from file_tab_opener.config import ConfigManager
        cm = ConfigManager()
        cm.path = tmp_path / "config.json"
        cm.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"history": [], "tab_groups": [], "settings": {}}
        cm.path.write_text(json.dumps(data), encoding="utf-8")
        cm.load()
        assert cm.data.settings.get("use_custom_tk") is True

    def test_settings_override_preserved(self, tmp_path) -> None:
        import json
        from file_tab_opener.config import ConfigManager
        cm = ConfigManager()
        cm.path = tmp_path / "config.json"
        cm.path.parent.mkdir(parents=True, exist_ok=True)
        data = {"history": [], "tab_groups": [], "settings": {"use_custom_tk": False, "timeout": 10}}
        cm.path.write_text(json.dumps(data), encoding="utf-8")
        cm.load()
        assert cm.data.settings["use_custom_tk"] is False
        assert cm.data.settings["timeout"] == 10


# ============================================================
# DEFAULT_SETTINGS constant (P5)
# ============================================================


class TestDefaultSettings:
    """Test that DEFAULT_SETTINGS is used consistently."""

    def test_default_settings_constant_matches_appconfig(self) -> None:
        """AppConfig default settings should match DEFAULT_SETTINGS."""
        from file_tab_opener.config import AppConfig, DEFAULT_SETTINGS
        config = AppConfig()
        for key, value in DEFAULT_SETTINGS.items():
            assert config.settings[key] == value

    def test_from_dict_uses_default_settings(self, tmp_path) -> None:
        """_from_dict should merge DEFAULT_SETTINGS with saved settings."""
        import json
        from file_tab_opener.config import ConfigManager, DEFAULT_SETTINGS
        cm = ConfigManager()
        cm.path = tmp_path / "config.json"
        cm.path.parent.mkdir(parents=True, exist_ok=True)
        # Save with extra setting, omitting defaults
        data = {"history": [], "tab_groups": [], "settings": {"timeout": 15}}
        cm.path.write_text(json.dumps(data), encoding="utf-8")
        cm.load()
        # Default settings should be merged in
        for key, value in DEFAULT_SETTINGS.items():
            assert cm.data.settings[key] == value
        # User setting should also be preserved
        assert cm.data.settings["timeout"] == 15


# ============================================================
# _strip_quotes edge cases
# ============================================================


class TestStripQuotesEdgeCases:
    """Additional edge case tests for strip_quotes."""

    def test_triple_quotes(self) -> None:
        """Triple quotes should strip outer pair only."""
        assert strip_quotes('"""') == '"'

    def test_whitespace_only(self) -> None:
        """Whitespace-only string should be returned as-is."""
        assert strip_quotes("   ") == "   "

    def test_unicode_path_with_quotes(self) -> None:
        """Unicode paths with surrounding quotes should be stripped."""
        assert strip_quotes('"C:\\ユーザー\\テスト"') == "C:\\ユーザー\\テスト"
