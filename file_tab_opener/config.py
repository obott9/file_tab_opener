"""
Configuration file management.

Handles reading/writing of history, tab groups, and app settings
to a JSON file. File location is OS-dependent.
"""

from __future__ import annotations

import json
import logging
import os
import platform
import re
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Final

log = logging.getLogger(__name__)


def strip_quotes(text: str) -> str:
    """Strip matching surrounding quotes (shell quoting artifacts).

    Shared utility used by both GUI (entry fields) and config (add_history).
    """
    for quote in ('"', "'"):
        if text.startswith(quote) and text.endswith(quote) and len(text) >= 2:
            return text[1:-1]
    return text

HISTORY_MAX: Final[int] = 50
DEFAULT_SETTINGS: Final[dict[str, Any]] = {"use_custom_tk": True}


def get_config_path() -> Path:
    """Return the OS-specific configuration file path."""
    system = platform.system()
    if system == "Darwin":
        return Path.home() / "Library" / "Application Support" / "FileTabOpener" / "config.json"
    elif system == "Windows":
        appdata = os.environ.get("APPDATA", "")
        if appdata:
            return Path(appdata) / "FileTabOpener" / "config.json"
        return Path.home() / "FileTabOpener" / "config.json"
    else:
        # Linux, etc.
        return Path.home() / ".config" / "file_tab_opener" / "config.json"


@dataclass
class HistoryEntry:
    """A single history entry with path, pin state, and usage tracking."""

    path: str
    pinned: bool = False
    last_used: str = ""
    use_count: int = 0

    def touch(self) -> None:
        """Update the last-used timestamp and increment the use count."""
        self.last_used = datetime.now().isoformat(timespec="seconds")
        self.use_count += 1


@dataclass
class TabGroup:
    """A named group of folder paths."""

    name: str
    paths: list[str] = field(default_factory=list)
    window_x: int | None = None
    window_y: int | None = None
    window_width: int | None = None
    window_height: int | None = None


@dataclass
class AppConfig:
    """Application-wide configuration data."""

    config_version: int = 1
    history: list[HistoryEntry] = field(default_factory=list)
    tab_groups: list[TabGroup] = field(default_factory=list)
    window_geometry: str = "800x600"
    settings: dict[str, Any] = field(default_factory=lambda: dict(DEFAULT_SETTINGS))


class ConfigManager:
    """Manages configuration read/write and history/tab-group operations."""

    def __init__(self) -> None:
        self.path: Path = get_config_path()
        self.data: AppConfig = AppConfig()

    def load(self) -> None:
        """Load configuration from file. Use defaults if the file is missing or corrupt."""
        if not self.path.exists():
            log.debug("Config file not found, using defaults: %s", self.path)
            return
        try:
            text = self.path.read_text(encoding="utf-8")
            d = json.loads(text)
            self.data = self._from_dict(d)
            log.debug(
                "Config loaded: %d history, %d tab groups",
                len(self.data.history), len(self.data.tab_groups),
            )
        except (json.JSONDecodeError, KeyError, TypeError, ValueError) as e:
            log.warning("Config file is corrupt, using defaults: %s", e)
            self.data = AppConfig()

    def save(self) -> None:
        """Write configuration to file atomically (tmp -> rename).

        Creates parent directories if needed.
        """
        self.path.parent.mkdir(parents=True, exist_ok=True)
        d = self._to_dict()
        text = json.dumps(d, ensure_ascii=False, indent=2)
        tmp_path = self.path.with_suffix(".tmp")
        try:
            tmp_path.write_text(text, encoding="utf-8")
            os.replace(tmp_path, self.path)
        except OSError:
            # Fallback: direct write if rename fails (e.g. cross-device)
            log.warning("Atomic rename failed, falling back to direct write")
            self.path.write_text(text, encoding="utf-8")
        log.debug("Config saved: %s", self.path)

    def _to_dict(self) -> dict[str, Any]:
        """Serialize AppConfig to a dictionary."""
        return {
            "config_version": self.data.config_version,
            "history": [
                {
                    "path": e.path,
                    "pinned": e.pinned,
                    "last_used": e.last_used,
                    "use_count": e.use_count,
                }
                for e in self.data.history
            ],
            "tab_groups": [
                {
                    "name": g.name,
                    "paths": list(g.paths),
                    "window_x": g.window_x,
                    "window_y": g.window_y,
                    "window_width": g.window_width,
                    "window_height": g.window_height,
                }
                for g in self.data.tab_groups
            ],
            "window_geometry": self.data.window_geometry,
            "settings": dict(self.data.settings),
        }

    @staticmethod
    def _from_dict(d: dict[str, Any]) -> AppConfig:
        """Deserialize a dictionary into AppConfig. Handles missing keys gracefully."""
        history: list[HistoryEntry] = []
        for item in d.get("history", []):
            history.append(HistoryEntry(
                path=item.get("path", ""),
                pinned=item.get("pinned", False),
                last_used=item.get("last_used", ""),
                use_count=item.get("use_count", 0),
            ))

        tab_groups: list[TabGroup] = []
        for item in d.get("tab_groups", []):
            # Compatibility: accept "folders" key as an alias for "paths"
            paths = item.get("paths", item.get("folders", []))
            tab_groups.append(TabGroup(
                name=item.get("name", ""),
                paths=list(paths),
                window_x=item.get("window_x"),
                window_y=item.get("window_y"),
                window_width=item.get("window_width"),
                window_height=item.get("window_height"),
            ))

        return AppConfig(
            config_version=d.get("config_version", 1),
            history=history,
            tab_groups=tab_groups,
            window_geometry=d.get("window_geometry", "800x600"),
            settings={**DEFAULT_SETTINGS, **d.get("settings", {})},
        )

    # --- History operations ---

    def add_history(self, path: str) -> None:
        """Add a path to history. Updates existing entry or appends a new one."""
        clean = strip_quotes(path.strip())
        normalized = os.path.normpath(clean)
        for entry in self.data.history:
            if os.path.normpath(entry.path) == normalized:
                entry.touch()
                log.debug("History updated (existing): %s", normalized)
                return
        new_entry = HistoryEntry(path=normalized)
        new_entry.touch()
        self.data.history.append(new_entry)
        self._trim_history()
        log.debug("History added (new): %s", normalized)

    def remove_history(self, path: str) -> None:
        """Remove a path from history."""
        normalized = os.path.normpath(path)
        self.data.history = [
            e for e in self.data.history
            if os.path.normpath(e.path) != normalized
        ]

    def clear_history(self, *, keep_pinned: bool = True) -> None:
        """Clear history. If keep_pinned is True, pinned entries are preserved."""
        before = len(self.data.history)
        if keep_pinned:
            self.data.history = [e for e in self.data.history if e.pinned]
        else:
            self.data.history.clear()
        log.info("History cleared: %d -> %d entries (keep_pinned=%s)", before, len(self.data.history), keep_pinned)

    def toggle_pin(self, path: str) -> None:
        """Toggle the pinned state of a history entry."""
        normalized = os.path.normpath(path)
        for entry in self.data.history:
            if os.path.normpath(entry.path) == normalized:
                entry.pinned = not entry.pinned
                log.debug("Pin toggled: %s -> pinned=%s", normalized, entry.pinned)
                return
        log.debug("toggle_pin: path not found in history: %s", normalized)

    def get_sorted_history(self) -> list[HistoryEntry]:
        """Return history sorted with pinned first, each group by most recent."""
        pinned = sorted(
            [e for e in self.data.history if e.pinned],
            key=lambda e: e.last_used,
            reverse=True,
        )
        unpinned = sorted(
            [e for e in self.data.history if not e.pinned],
            key=lambda e: e.last_used,
            reverse=True,
        )
        return pinned + unpinned

    def _trim_history(self) -> None:
        """Remove the oldest unpinned entries when history exceeds HISTORY_MAX.

        O(n log n) implementation: sort unpinned by last_used descending,
        keep only the newest ones, then recombine with pinned entries.
        """
        if len(self.data.history) <= HISTORY_MAX:
            return
        pinned = [e for e in self.data.history if e.pinned]
        unpinned = [e for e in self.data.history if not e.pinned]
        keep_count = max(HISTORY_MAX - len(pinned), 0)
        # Sort unpinned by last_used descending, keep newest
        unpinned.sort(key=lambda e: e.last_used, reverse=True)
        self.data.history = pinned + unpinned[:keep_count]

    # --- Tab group operations ---

    def add_tab_group(self, name: str) -> TabGroup | None:
        """Create a new empty tab group. Returns None if the name already exists or is empty."""
        if not name or not name.strip():
            log.debug("add_tab_group: empty name rejected")
            return None
        if self.get_tab_group(name) is not None:
            log.debug("add_tab_group: name already exists: %s", name)
            return None
        group = TabGroup(name=name)
        self.data.tab_groups.append(group)
        log.info("Tab group added: %s", name)
        return group

    def delete_tab_group(self, name: str) -> None:
        """Delete a tab group by name."""
        self.data.tab_groups = [g for g in self.data.tab_groups if g.name != name]
        log.info("Tab group deleted: %s", name)

    def rename_tab_group(self, old_name: str, new_name: str) -> None:
        """Rename a tab group."""
        for group in self.data.tab_groups:
            if group.name == old_name:
                group.name = new_name
                log.info("Tab group renamed: %s -> %s", old_name, new_name)
                return
        log.debug("rename_tab_group: not found: %s", old_name)

    def get_tab_group(self, name: str) -> TabGroup | None:
        """Get a tab group by name. Returns None if not found."""
        for group in self.data.tab_groups:
            if group.name == name:
                return group
        return None

    def add_path_to_group(self, group_name: str, path: str) -> None:
        """Add a path to a tab group."""
        group = self.get_tab_group(group_name)
        if group:
            normalized = os.path.normpath(path)
            group.paths.append(normalized)
            log.debug("Path added to group '%s': %s", group_name, normalized)

    def remove_path_from_group(self, group_name: str, index: int) -> None:
        """Remove a path from a tab group by index."""
        group = self.get_tab_group(group_name)
        if group and 0 <= index < len(group.paths):
            removed = group.paths.pop(index)
            log.debug("Path removed from group '%s': [%d] %s", group_name, index, removed)

    def move_tab_group(self, old_index: int, new_index: int) -> None:
        """Reorder a tab group."""
        groups = self.data.tab_groups
        if 0 <= old_index < len(groups) and 0 <= new_index < len(groups):
            item = groups.pop(old_index)
            groups.insert(new_index, item)

    def copy_tab_group(self, name: str) -> TabGroup | None:
        """Copy a tab group with an auto-incremented name.

        Extracts the base name by stripping a trailing number suffix,
        then finds the next available number starting from 1.
        Examples:
            'テスト'   -> 'テスト 1' -> 'テスト 2' -> ...
            'テスト 3' -> 'テスト 4' (or next available)
        """
        source = self.get_tab_group(name)
        if not source:
            log.debug("copy_tab_group: source not found: %s", name)
            return None
        # Extract base name: strip trailing ' <digits>'
        m = re.match(r'^(.*?)\s+(\d+)$', name)
        base = m.group(1) if m else name
        existing_names = {g.name for g in self.data.tab_groups}
        suffix = 1
        while f"{base} {suffix}" in existing_names:
            suffix += 1
        new_name = f"{base} {suffix}"
        new_group = TabGroup(
            name=new_name,
            paths=list(source.paths),
            window_x=source.window_x,
            window_y=source.window_y,
            window_width=source.window_width,
            window_height=source.window_height,
        )
        self.data.tab_groups.append(new_group)
        log.info("Tab group copied: %s -> %s (%d paths)", name, new_name, len(new_group.paths))
        return new_group

    def move_path_in_group(self, group_name: str, old_index: int, new_index: int) -> None:
        """Reorder a path within a tab group."""
        group = self.get_tab_group(group_name)
        if group and 0 <= old_index < len(group.paths) and 0 <= new_index < len(group.paths):
            item = group.paths.pop(old_index)
            group.paths.insert(new_index, item)
