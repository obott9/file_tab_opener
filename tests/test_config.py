"""Tests for config module.

Covers: ConfigManager load/save, history CRUD, tab group CRUD,
serialization round-trip, edge cases, and data integrity.
"""

from __future__ import annotations

import json
import os
from pathlib import Path

import pytest

from file_tab_opener.config import AppConfig, ConfigManager, HistoryEntry, TabGroup, HISTORY_MAX


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture
def tmp_config(tmp_path: Path) -> ConfigManager:
    """Create a ConfigManager that writes to a temp directory."""
    cm = ConfigManager()
    cm.path = tmp_path / "config.json"
    return cm


@pytest.fixture
def populated_config(tmp_config: ConfigManager) -> ConfigManager:
    """ConfigManager pre-loaded with sample data."""
    tmp_config.add_history(r"C:\Users\test\Documents")
    tmp_config.add_history(r"C:\Users\test\Downloads")
    tmp_config.add_tab_group("Work")
    tmp_config.add_path_to_group("Work", r"C:\Projects\alpha")
    tmp_config.add_path_to_group("Work", r"C:\Projects\beta")
    tmp_config.add_tab_group("Personal")
    tmp_config.add_path_to_group("Personal", r"C:\Users\test\Music")
    return tmp_config


# ============================================================
# Load / Save
# ============================================================


class TestLoadSave:
    """Test configuration persistence."""

    def test_load_missing_file(self, tmp_config: ConfigManager) -> None:
        """Loading a non-existent file should use defaults without error."""
        tmp_config.load()
        assert tmp_config.data.history == []
        assert tmp_config.data.tab_groups == []
        assert tmp_config.data.window_geometry == "800x600"

    def test_save_creates_parent_dirs(self, tmp_path: Path) -> None:
        """Save should create parent directories if they don't exist."""
        cm = ConfigManager()
        cm.path = tmp_path / "nested" / "deep" / "config.json"
        cm.save()
        assert cm.path.exists()

    def test_round_trip(self, populated_config: ConfigManager) -> None:
        """Data survives a save → load cycle."""
        populated_config.save()

        cm2 = ConfigManager()
        cm2.path = populated_config.path
        cm2.load()

        assert len(cm2.data.history) == 2
        assert len(cm2.data.tab_groups) == 2
        assert cm2.data.tab_groups[0].name == "Work"
        assert len(cm2.data.tab_groups[0].paths) == 2

    def test_load_corrupt_json(self, tmp_config: ConfigManager) -> None:
        """Corrupt JSON should be handled gracefully, falling back to defaults."""
        tmp_config.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_config.path.write_text("{invalid json!!!", encoding="utf-8")
        tmp_config.load()
        assert tmp_config.data.history == []
        assert tmp_config.data.tab_groups == []

    def test_load_valid_json_missing_keys(self, tmp_config: ConfigManager) -> None:
        """Valid JSON with missing keys should use defaults for missing fields."""
        tmp_config.path.parent.mkdir(parents=True, exist_ok=True)
        tmp_config.path.write_text('{"history": []}', encoding="utf-8")
        tmp_config.load()
        assert tmp_config.data.tab_groups == []
        assert tmp_config.data.window_geometry == "800x600"

    def test_save_utf8_paths(self, tmp_config: ConfigManager) -> None:
        """Paths with non-ASCII characters should be saved correctly."""
        tmp_config.data.history.append(
            HistoryEntry(path="C:\\ユーザー\\テスト")
        )
        tmp_config.save()
        text = tmp_config.path.read_text(encoding="utf-8")
        assert "ユーザー" in text

    def test_json_structure(self, populated_config: ConfigManager) -> None:
        """Saved JSON should have the expected top-level keys."""
        populated_config.save()
        data = json.loads(populated_config.path.read_text(encoding="utf-8"))
        assert set(data.keys()) == {"history", "tab_groups", "window_geometry", "settings"}
        assert isinstance(data["history"], list)
        assert isinstance(data["tab_groups"], list)


# ============================================================
# History operations
# ============================================================


class TestHistory:
    """Test history CRUD operations."""

    def test_add_history(self, tmp_config: ConfigManager) -> None:
        """Adding a path should create a history entry with use_count=1."""
        tmp_config.add_history(r"C:\test")
        assert len(tmp_config.data.history) == 1
        entry = tmp_config.data.history[0]
        assert entry.use_count == 1
        assert entry.last_used != ""

    def test_add_duplicate_increments_count(self, tmp_config: ConfigManager) -> None:
        """Adding the same path again should increment use_count, not create a duplicate."""
        tmp_config.add_history(r"C:\test")
        tmp_config.add_history(r"C:\test")
        assert len(tmp_config.data.history) == 1
        assert tmp_config.data.history[0].use_count == 2

    def test_add_normalizes_path(self, tmp_config: ConfigManager) -> None:
        """Paths should be normalized (e.g. C:/test -> C:\\test)."""
        tmp_config.add_history("C:/foo/bar/../baz")
        entry = tmp_config.data.history[0]
        assert entry.path == os.path.normpath("C:/foo/bar/../baz")

    def test_add_strips_quotes(self, tmp_config: ConfigManager) -> None:
        """Surrounding double quotes (from Explorer's Copy Path) should be stripped."""
        tmp_config.add_history('"C:\\Users\\test"')
        entry = tmp_config.data.history[0]
        assert not entry.path.startswith('"')
        assert not entry.path.endswith('"')

    def test_add_strips_whitespace(self, tmp_config: ConfigManager) -> None:
        """Leading/trailing whitespace should be stripped."""
        tmp_config.add_history("  C:\\test  ")
        entry = tmp_config.data.history[0]
        assert entry.path == os.path.normpath("C:\\test")

    def test_remove_history(self, tmp_config: ConfigManager) -> None:
        """Removing a path should delete it from history."""
        tmp_config.add_history(r"C:\a")
        tmp_config.add_history(r"C:\b")
        tmp_config.remove_history(r"C:\a")
        assert len(tmp_config.data.history) == 1
        assert tmp_config.data.history[0].path == os.path.normpath(r"C:\b")

    def test_remove_nonexistent(self, tmp_config: ConfigManager) -> None:
        """Removing a non-existent path should be a no-op."""
        tmp_config.add_history(r"C:\a")
        tmp_config.remove_history(r"C:\nonexistent")
        assert len(tmp_config.data.history) == 1

    def test_clear_history_keeps_pinned(self, tmp_config: ConfigManager) -> None:
        """Clearing history with keep_pinned=True preserves pinned entries."""
        tmp_config.add_history(r"C:\pinned")
        tmp_config.add_history(r"C:\unpinned")
        tmp_config.toggle_pin(r"C:\pinned")
        tmp_config.clear_history(keep_pinned=True)
        assert len(tmp_config.data.history) == 1
        assert tmp_config.data.history[0].pinned is True

    def test_clear_history_all(self, tmp_config: ConfigManager) -> None:
        """Clearing history with keep_pinned=False removes everything."""
        tmp_config.add_history(r"C:\pinned")
        tmp_config.toggle_pin(r"C:\pinned")
        tmp_config.add_history(r"C:\unpinned")
        tmp_config.clear_history(keep_pinned=False)
        assert len(tmp_config.data.history) == 0

    def test_toggle_pin(self, tmp_config: ConfigManager) -> None:
        """Toggling pin should flip the pinned state."""
        tmp_config.add_history(r"C:\test")
        assert tmp_config.data.history[0].pinned is False
        tmp_config.toggle_pin(r"C:\test")
        assert tmp_config.data.history[0].pinned is True
        tmp_config.toggle_pin(r"C:\test")
        assert tmp_config.data.history[0].pinned is False

    def test_toggle_pin_nonexistent(self, tmp_config: ConfigManager) -> None:
        """Toggling pin on a non-existent path should be a no-op."""
        tmp_config.toggle_pin(r"C:\nonexistent")  # Should not raise

    def test_get_sorted_history(self, tmp_config: ConfigManager) -> None:
        """Sorted history should have pinned entries first."""
        tmp_config.add_history(r"C:\a")
        tmp_config.add_history(r"C:\b")
        tmp_config.add_history(r"C:\c")
        tmp_config.toggle_pin(r"C:\b")

        result = tmp_config.get_sorted_history()
        assert result[0].pinned is True
        assert result[0].path == os.path.normpath(r"C:\b")

    def test_trim_history_respects_max(self, tmp_config: ConfigManager) -> None:
        """History should not exceed HISTORY_MAX entries."""
        for i in range(HISTORY_MAX + 10):
            tmp_config.add_history(f"C:\\folder_{i:03d}")
        assert len(tmp_config.data.history) <= HISTORY_MAX

    def test_trim_preserves_pinned(self, tmp_config: ConfigManager) -> None:
        """Trimming should never remove pinned entries."""
        # Pin one entry first
        tmp_config.add_history(r"C:\pinned_entry")
        tmp_config.toggle_pin(r"C:\pinned_entry")

        # Fill history to max
        for i in range(HISTORY_MAX + 5):
            tmp_config.add_history(f"C:\\folder_{i:03d}")

        pinned = [e for e in tmp_config.data.history if e.pinned]
        assert len(pinned) >= 1
        assert any(e.path == os.path.normpath(r"C:\pinned_entry") for e in pinned)


# ============================================================
# HistoryEntry
# ============================================================


class TestHistoryEntry:
    """Test HistoryEntry dataclass."""

    def test_touch_updates_fields(self) -> None:
        """touch() should update last_used and increment use_count."""
        entry = HistoryEntry(path="C:\\test")
        assert entry.use_count == 0
        assert entry.last_used == ""
        entry.touch()
        assert entry.use_count == 1
        assert entry.last_used != ""

    def test_touch_increments(self) -> None:
        """Multiple touch() calls should increment use_count."""
        entry = HistoryEntry(path="C:\\test")
        entry.touch()
        entry.touch()
        entry.touch()
        assert entry.use_count == 3

    def test_defaults(self) -> None:
        """Default values should be correct."""
        entry = HistoryEntry(path="C:\\test")
        assert entry.pinned is False
        assert entry.last_used == ""
        assert entry.use_count == 0


# ============================================================
# Tab group operations
# ============================================================


class TestTabGroups:
    """Test tab group CRUD operations."""

    def test_add_tab_group(self, tmp_config: ConfigManager) -> None:
        """Adding a tab group should create an empty group."""
        group = tmp_config.add_tab_group("Work")
        assert group.name == "Work"
        assert group.paths == []
        assert len(tmp_config.data.tab_groups) == 1

    def test_delete_tab_group(self, tmp_config: ConfigManager) -> None:
        """Deleting a tab group should remove it."""
        tmp_config.add_tab_group("Work")
        tmp_config.add_tab_group("Play")
        tmp_config.delete_tab_group("Work")
        assert len(tmp_config.data.tab_groups) == 1
        assert tmp_config.data.tab_groups[0].name == "Play"

    def test_delete_nonexistent_group(self, tmp_config: ConfigManager) -> None:
        """Deleting a non-existent group should be a no-op."""
        tmp_config.add_tab_group("Work")
        tmp_config.delete_tab_group("Nonexistent")
        assert len(tmp_config.data.tab_groups) == 1

    def test_rename_tab_group(self, tmp_config: ConfigManager) -> None:
        """Renaming a tab group should update its name."""
        tmp_config.add_tab_group("Old Name")
        tmp_config.rename_tab_group("Old Name", "New Name")
        assert tmp_config.data.tab_groups[0].name == "New Name"

    def test_rename_nonexistent(self, tmp_config: ConfigManager) -> None:
        """Renaming a non-existent group should be a no-op."""
        tmp_config.rename_tab_group("Nonexistent", "New")  # Should not raise

    def test_get_tab_group(self, tmp_config: ConfigManager) -> None:
        """get_tab_group should return the group or None."""
        tmp_config.add_tab_group("Work")
        assert tmp_config.get_tab_group("Work") is not None
        assert tmp_config.get_tab_group("Nonexistent") is None

    def test_add_path_to_group(self, tmp_config: ConfigManager) -> None:
        """Adding a path to a group should normalize and append it."""
        tmp_config.add_tab_group("Work")
        tmp_config.add_path_to_group("Work", "C:/test/path")
        group = tmp_config.get_tab_group("Work")
        assert group is not None
        assert len(group.paths) == 1
        assert group.paths[0] == os.path.normpath("C:/test/path")

    def test_add_path_to_nonexistent_group(self, tmp_config: ConfigManager) -> None:
        """Adding a path to a non-existent group should be a no-op."""
        tmp_config.add_path_to_group("Nonexistent", "C:\\test")
        # Should not raise

    def test_remove_path_from_group(self, tmp_config: ConfigManager) -> None:
        """Removing a path by index should work correctly."""
        tmp_config.add_tab_group("Work")
        tmp_config.add_path_to_group("Work", r"C:\a")
        tmp_config.add_path_to_group("Work", r"C:\b")
        tmp_config.add_path_to_group("Work", r"C:\c")
        tmp_config.remove_path_from_group("Work", 1)
        group = tmp_config.get_tab_group("Work")
        assert group is not None
        assert len(group.paths) == 2
        assert os.path.normpath(r"C:\b") not in group.paths

    def test_remove_path_invalid_index(self, tmp_config: ConfigManager) -> None:
        """Removing with an invalid index should be a no-op."""
        tmp_config.add_tab_group("Work")
        tmp_config.add_path_to_group("Work", r"C:\a")
        tmp_config.remove_path_from_group("Work", 99)
        tmp_config.remove_path_from_group("Work", -1)
        group = tmp_config.get_tab_group("Work")
        assert group is not None
        assert len(group.paths) == 1

    def test_move_path_in_group(self, tmp_config: ConfigManager) -> None:
        """Moving a path should reorder the list."""
        tmp_config.add_tab_group("Work")
        tmp_config.add_path_to_group("Work", r"C:\a")
        tmp_config.add_path_to_group("Work", r"C:\b")
        tmp_config.add_path_to_group("Work", r"C:\c")
        # Move "C:\a" (index 0) to index 2
        tmp_config.move_path_in_group("Work", 0, 2)
        group = tmp_config.get_tab_group("Work")
        assert group is not None
        assert group.paths[0] == os.path.normpath(r"C:\b")
        assert group.paths[2] == os.path.normpath(r"C:\a")

    def test_move_path_invalid_indices(self, tmp_config: ConfigManager) -> None:
        """Moving with invalid indices should be a no-op."""
        tmp_config.add_tab_group("Work")
        tmp_config.add_path_to_group("Work", r"C:\a")
        tmp_config.move_path_in_group("Work", 0, 99)
        tmp_config.move_path_in_group("Work", -1, 0)
        group = tmp_config.get_tab_group("Work")
        assert group is not None
        assert len(group.paths) == 1


# ============================================================
# Copy tab group (base name extraction)
# ============================================================


class TestCopyTabGroup:
    """Test copy_tab_group with base-name extraction and sequential naming."""

    def test_copy_basic(self, tmp_config: ConfigManager) -> None:
        """'テスト' -> 'テスト 1'"""
        tmp_config.add_tab_group("テスト")
        result = tmp_config.copy_tab_group("テスト")
        assert result is not None
        assert result.name == "テスト 1"

    def test_copy_sequential(self, tmp_config: ConfigManager) -> None:
        """'テスト' -> 'テスト 1' -> 'テスト 2'"""
        tmp_config.add_tab_group("テスト")
        tmp_config.copy_tab_group("テスト")
        result = tmp_config.copy_tab_group("テスト")
        assert result is not None
        assert result.name == "テスト 2"

    def test_copy_numbered_tab(self, tmp_config: ConfigManager) -> None:
        """'テスト 1' -> 'テスト 2' (extracts base 'テスト')"""
        tmp_config.add_tab_group("テスト 1")
        result = tmp_config.copy_tab_group("テスト 1")
        assert result is not None
        assert result.name == "テスト 2"

    def test_copy_numbered_tab_skips_existing(self, tmp_config: ConfigManager) -> None:
        """'テスト 3' with 1,2,3 existing -> 'テスト 4'"""
        tmp_config.add_tab_group("テスト 1")
        tmp_config.add_tab_group("テスト 2")
        tmp_config.add_tab_group("テスト 3")
        result = tmp_config.copy_tab_group("テスト 3")
        assert result is not None
        assert result.name == "テスト 4"

    def test_copy_fills_gap(self, tmp_config: ConfigManager) -> None:
        """'テスト 3' with only 3 existing -> 'テスト 1' (fills gap)"""
        tmp_config.add_tab_group("テスト 3")
        result = tmp_config.copy_tab_group("テスト 3")
        assert result is not None
        assert result.name == "テスト 1"

    def test_copy_preserves_paths(self, tmp_config: ConfigManager) -> None:
        """Copy should preserve paths from source."""
        tmp_config.add_tab_group("Work")
        tmp_config.add_path_to_group("Work", r"C:\Projects")
        result = tmp_config.copy_tab_group("Work")
        assert result is not None
        assert len(result.paths) == 1

    def test_copy_nonexistent(self, tmp_config: ConfigManager) -> None:
        """Copying non-existent group returns None."""
        result = tmp_config.copy_tab_group("NoSuch")
        assert result is None


# ============================================================
# Serialization compatibility
# ============================================================


class TestSerialization:
    """Test JSON serialization/deserialization edge cases."""

    def test_folders_key_compatibility(self, tmp_config: ConfigManager) -> None:
        """Legacy 'folders' key should be accepted as an alias for 'paths'."""
        tmp_config.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "history": [],
            "tab_groups": [
                {"name": "Legacy", "folders": ["C:\\old\\path"]}
            ],
        }
        tmp_config.path.write_text(json.dumps(data), encoding="utf-8")
        tmp_config.load()
        group = tmp_config.get_tab_group("Legacy")
        assert group is not None
        assert group.paths == ["C:\\old\\path"]

    def test_missing_history_fields_default(self, tmp_config: ConfigManager) -> None:
        """History entries with missing fields should use defaults."""
        tmp_config.path.parent.mkdir(parents=True, exist_ok=True)
        data = {
            "history": [{"path": "C:\\test"}],
            "tab_groups": [],
        }
        tmp_config.path.write_text(json.dumps(data), encoding="utf-8")
        tmp_config.load()
        entry = tmp_config.data.history[0]
        assert entry.pinned is False
        assert entry.last_used == ""
        assert entry.use_count == 0

    def test_settings_preserved(self, tmp_config: ConfigManager) -> None:
        """Custom settings should survive round-trip."""
        tmp_config.data.settings["use_custom_tk"] = False
        tmp_config.data.settings["theme"] = "dark"
        tmp_config.save()

        cm2 = ConfigManager()
        cm2.path = tmp_config.path
        cm2.load()
        assert cm2.data.settings["use_custom_tk"] is False
        assert cm2.data.settings["theme"] == "dark"

    def test_window_geometry_preserved(self, tmp_config: ConfigManager) -> None:
        """Window geometry should survive round-trip."""
        tmp_config.data.window_geometry = "1024x768+100+50"
        tmp_config.save()

        cm2 = ConfigManager()
        cm2.path = tmp_config.path
        cm2.load()
        assert cm2.data.window_geometry == "1024x768+100+50"
