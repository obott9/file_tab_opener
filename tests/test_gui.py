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
