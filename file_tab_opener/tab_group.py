"""
Tab group section for File Tab Opener GUI.

Bottom section: tab bar + path list + action buttons + Open as Tabs button.
"""

from __future__ import annotations

import logging
import os
import subprocess
import tkinter as tk
import tkinter.ttk as ttk
from collections.abc import Callable
from pathlib import Path

from file_tab_opener import is_unc_path
from tkinter import filedialog, messagebox, simpledialog
from typing import Any

from file_tab_opener.config import ConfigManager
from file_tab_opener.i18n import t
from file_tab_opener.widgets import (
    CTK_AVAILABLE,
    IS_MAC,
    IS_WIN,
    Frame,
    Button,
    Label,
    Entry,
    TabView,
    _strip_quotes,
    _setup_placeholder,
    _is_placeholder_active,
)

log = logging.getLogger(__name__)

# Import ctk only when available
if CTK_AVAILABLE:
    import customtkinter as ctk

# Finder/Explorer minimum window size (macOS Finder enforces these)
MIN_WINDOW_WIDTH = 528
MIN_WINDOW_HEIGHT = 308


class TabGroupSection:
    """Bottom section: tab bar + path list + action buttons + Open as Tabs button."""

    def __init__(
        self,
        parent: Any,
        config: ConfigManager,
        on_open_tabs: Callable[[list[str], tuple[int, int, int, int] | None], None],
    ) -> None:
        self.config = config
        self.on_open_tabs = on_open_tabs
        self.current_tab_name: str | None = None
        self._opening: bool = False

        self.frame = Frame(parent)
        self._build_widgets()
        self._load_tabs_from_config()

    def _build_widgets(self) -> None:
        """Build all widgets in the tab group section."""
        # --- Tab management bar ---
        tab_bar = Frame(self.frame)
        tab_bar.pack(fill=tk.X, pady=(0, 5))

        Button(tab_bar, text=t("tab.add"), command=self._on_add_tab, width=10).pack(
            side=tk.LEFT, padx=2
        )
        Button(
            tab_bar, text=t("tab.delete"), command=self._on_delete_tab, width=10
        ).pack(side=tk.LEFT, padx=2)
        Button(
            tab_bar, text=t("tab.rename"), command=self._on_rename_tab, width=10
        ).pack(side=tk.LEFT, padx=2)
        Button(
            tab_bar, text=t("tab.copy"), command=self._on_copy_tab, width=10
        ).pack(side=tk.LEFT, padx=2)
        Button(
            tab_bar, text=t("tab.move_left"), command=self._on_move_tab_left, width=3
        ).pack(side=tk.LEFT, padx=(10, 0))
        Button(
            tab_bar, text=t("tab.move_right"), command=self._on_move_tab_right, width=3
        ).pack(side=tk.LEFT, padx=2)

        # --- Tab view (tab names only, no expand) ---
        self.tab_view = TabView(self.frame, on_tab_changed=self._on_tab_changed)
        self.tab_view.pack(fill=tk.X)

        # --- Window geometry settings (per-tab) ---
        geom_frame = Frame(self.frame)
        geom_frame.pack(fill=tk.X, pady=(5, 0))

        geom_entry_width = 70 if CTK_AVAILABLE else 7

        Label(geom_frame, text=t("window.x")).pack(side=tk.LEFT, padx=(0, 2))
        self._geom_x_entry = Entry(geom_frame, width=geom_entry_width)
        self._geom_x_entry.pack(side=tk.LEFT, padx=(0, 8))

        Label(geom_frame, text=t("window.y")).pack(side=tk.LEFT, padx=(0, 2))
        self._geom_y_entry = Entry(geom_frame, width=geom_entry_width)
        self._geom_y_entry.pack(side=tk.LEFT, padx=(0, 8))

        Label(geom_frame, text=t("window.width")).pack(side=tk.LEFT, padx=(0, 2))
        self._geom_w_entry = Entry(geom_frame, width=geom_entry_width)
        self._geom_w_entry.pack(side=tk.LEFT, padx=(0, 8))

        Label(geom_frame, text=t("window.height")).pack(side=tk.LEFT, padx=(0, 2))
        self._geom_h_entry = Entry(geom_frame, width=geom_entry_width)
        self._geom_h_entry.pack(side=tk.LEFT, padx=(0, 8))

        if IS_MAC:
            Button(
                geom_frame, text=t("window.get_from_finder"),
                command=self._on_get_finder_bounds, width=14,
            ).pack(side=tk.LEFT)
        elif IS_WIN:
            Button(
                geom_frame, text=t("window.get_from_explorer"),
                command=self._on_get_explorer_bounds, width=18,
            ).pack(side=tk.LEFT)

        for entry in (self._geom_x_entry, self._geom_y_entry,
                       self._geom_w_entry, self._geom_h_entry):
            entry.bind("<FocusOut>", lambda e: self._save_geometry())
            entry.bind("<Return>", lambda e: self._save_geometry())

        # --- Content area (listbox + buttons) ---
        content = Frame(self.frame)
        content.pack(fill=tk.BOTH, expand=True, pady=5)

        # Listbox (left side)
        list_frame = ttk.Frame(content)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=10)
        scrollbar_y = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.listbox.yview
        )
        scrollbar_x = ttk.Scrollbar(
            list_frame, orient=tk.HORIZONTAL, command=self.listbox.xview
        )
        self.listbox.configure(
            yscrollcommand=scrollbar_y.set,
            xscrollcommand=scrollbar_x.set,
        )
        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        self.listbox.pack(side=tk.TOP, fill=tk.BOTH, expand=True)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)

        # Copy selected path to entry field
        self.listbox.bind("<<ListboxSelect>>", self._on_listbox_select)

        # Adjust listbox theme when using customtkinter
        if CTK_AVAILABLE:
            try:
                mode = ctk.get_appearance_mode()
                if mode == "Dark":
                    self.listbox.configure(
                        bg="#2b2b2b", fg="#ffffff", selectbackground="#1f6aa5"
                    )
                else:
                    self.listbox.configure(
                        bg="#ffffff", fg="#000000", selectbackground="#1f6aa5"
                    )
            except Exception as e:
                log.debug("Theme detection failed for listbox: %s", e)

        # Action buttons (right side)
        btn_frame = Frame(content)
        btn_frame.pack(side=tk.RIGHT, fill=tk.Y, padx=(5, 0))

        for text, cmd in [
            (t("path.move_up"), self._on_move_up),
            (t("path.move_down"), self._on_move_down),
            (t("path.add"), self._on_add_path),
            (t("path.remove"), self._on_remove_path),
            (t("path.browse"), self._on_browse),
        ]:
            Button(btn_frame, text=text, command=cmd, width=10).pack(
                pady=2, fill=tk.X
            )

        # --- Path entry ---
        entry_frame = Frame(self.frame)
        entry_frame.pack(fill=tk.X, pady=(0, 5))

        if CTK_AVAILABLE:
            self.path_entry = Entry(entry_frame, placeholder_text=t("path.placeholder"))
        else:
            self.path_entry = Entry(entry_frame)
            _setup_placeholder(self.path_entry, t("path.placeholder"))
            # macOS: select all on focus (ttk only; CTkEntry handles this internally)
            if IS_MAC:
                self.path_entry.bind(
                    "<FocusIn>", lambda e: e.widget.selection_range(0, tk.END), add="+",
                )
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Enter key to add path
        self.path_entry.bind("<Return>", lambda e: self._on_add_path())

        # --- Open as Tabs button ---
        self.open_btn = Button(
            self.frame, text=t("tab.open_as_tabs"), command=self._on_open_as_tabs
        )
        self.open_btn.pack(fill=tk.X, pady=(5, 0), ipady=8)

    def _load_tabs_from_config(self) -> None:
        """Restore tab groups from the config file. Create a default tab if empty."""
        if not self.config.data.tab_groups:
            self.config.add_tab_group("Tab 1")
            self.config.save()
        for group in self.config.data.tab_groups:
            self.tab_view.add_tab(group.name)
        names = self.tab_view.tab_names()
        if names:
            self.tab_view.set_current_tab(names[0])
            self.current_tab_name = names[0]
            self._refresh_listbox()
            self._load_geometry()

    def restore_tab_state(self) -> None:
        """Refresh the listbox and geometry fields for the current tab."""
        self._refresh_listbox()
        self._load_geometry()

    def _on_tab_changed(self, tab_name: str) -> None:
        """Handle tab selection change."""
        self._save_geometry()
        self.current_tab_name = tab_name
        self.restore_tab_state()

    def _refresh_listbox(self) -> None:
        """Update the listbox with paths from the current tab group."""
        self.listbox.delete(0, tk.END)
        if not self.current_tab_name:
            return
        group = self.config.get_tab_group(self.current_tab_name)
        if group:
            for path in group.paths:
                self.listbox.insert(tk.END, path)
        self.listbox.xview_moveto(0)

    def _on_add_tab(self) -> None:
        """Handle the Add Tab button click."""
        top = self.frame.winfo_toplevel()
        name = simpledialog.askstring(
            t("tab.add_dialog_title"), t("tab.add_dialog_prompt"), parent=top
        )
        if not name or not name.strip():
            return
        name = name.strip()
        if self.config.get_tab_group(name):
            messagebox.showwarning(
                t("tab.duplicate_title"),
                t("tab.duplicate_msg", name=name),
                parent=top,
            )
            return
        self.config.add_tab_group(name)
        self.config.save()
        self.tab_view.add_tab(name)
        self.tab_view.set_current_tab(name)
        self.current_tab_name = name
        self._refresh_listbox()
        log.info("Tab added: %s", name)

    def _on_delete_tab(self) -> None:
        """Handle the Delete Tab button click."""
        name = self.tab_view.get_current_tab_name()
        if not name:
            return
        top = self.frame.winfo_toplevel()
        result = messagebox.askyesno(
            t("tab.delete_confirm_title"),
            t("tab.delete_confirm_msg", name=name),
            parent=top,
        )
        if result:
            log.info("Tab deleted: %s", name)
            self.config.delete_tab_group(name)
            self.config.save()
            self.tab_view.delete_tab(name)
            # delete_tab selects the right neighbor (or left if rightmost)
            new_current = self.tab_view.get_current_tab_name()
            if new_current:
                self.tab_view.set_current_tab(new_current)
            self.current_tab_name = new_current
            self._refresh_listbox()
            self._load_geometry()

    def _on_rename_tab(self) -> None:
        """Handle the Rename Tab button click."""
        old_name = self.tab_view.get_current_tab_name()
        if not old_name:
            return
        top = self.frame.winfo_toplevel()
        new_name = simpledialog.askstring(
            t("tab.rename_dialog_title"),
            t("tab.rename_dialog_prompt"),
            initialvalue=old_name,
            parent=top,
        )
        if not new_name or not new_name.strip() or new_name.strip() == old_name:
            return
        new_name = new_name.strip()
        if self.config.get_tab_group(new_name):
            messagebox.showwarning(
                t("tab.duplicate_title"),
                t("tab.duplicate_msg", name=new_name),
                parent=top,
            )
            return
        self.config.rename_tab_group(old_name, new_name)
        self.config.save()
        self.tab_view.rename_tab(old_name, new_name)
        self.current_tab_name = new_name
        log.info("Tab renamed: %s -> %s", old_name, new_name)

    def _on_copy_tab(self) -> None:
        """Handle the Copy Tab button click."""
        name = self.tab_view.get_current_tab_name()
        if not name:
            return
        new_group = self.config.copy_tab_group(name)
        if not new_group:
            return
        self.config.save()
        self.tab_view.add_tab(new_group.name)
        self.tab_view.set_current_tab(new_group.name)
        self.current_tab_name = new_group.name
        self._refresh_listbox()
        self._load_geometry()
        log.info("Tab copied: %s -> %s", name, new_group.name)

    def _on_move_tab_left(self) -> None:
        """Move the current tab one position to the left."""
        name = self.tab_view.get_current_tab_name()
        if not name:
            return
        names = self.tab_view.tab_names()
        idx = names.index(name)
        if idx <= 0:
            return
        self.config.move_tab_group(idx, idx - 1)
        self.config.save()
        self.tab_view.move_tab(idx, idx - 1)

    def _on_move_tab_right(self) -> None:
        """Move the current tab one position to the right."""
        name = self.tab_view.get_current_tab_name()
        if not name:
            return
        names = self.tab_view.tab_names()
        idx = names.index(name)
        if idx >= len(names) - 1:
            return
        self.config.move_tab_group(idx, idx + 1)
        self.config.save()
        self.tab_view.move_tab(idx, idx + 1)

    def _on_add_path(self) -> None:
        """Handle the Add Path button click or Enter key in path entry."""
        if _is_placeholder_active(self.path_entry):
            return
        raw = self.path_entry.get().strip()
        path = _strip_quotes(raw)
        if not path:
            return
        top = self.frame.winfo_toplevel()
        if not self.current_tab_name:
            messagebox.showinfo(
                t("tab.no_tab_title"), t("tab.no_tab_msg"), parent=top
            )
            return
        expanded = os.path.expanduser(path)
        if not (is_unc_path(expanded) or Path(expanded).is_dir()):
            messagebox.showwarning(
                t("path.invalid_title"),
                t("path.invalid_msg", path=path),
                parent=top,
            )
            return
        self.config.add_path_to_group(self.current_tab_name, expanded)
        self.config.save()
        self._refresh_listbox()
        self.path_entry.delete(0, tk.END)
        log.info("Path added to '%s': %s", self.current_tab_name, expanded)

    def _on_remove_path(self) -> None:
        """Handle the Remove Path button click."""
        sel = self.listbox.curselection()
        if not sel or not self.current_tab_name:
            return
        removed_path = self.listbox.get(sel[0])
        self.config.remove_path_from_group(self.current_tab_name, sel[0])
        self.config.save()
        self._refresh_listbox()
        log.info("Path removed from '%s': %s", self.current_tab_name, removed_path)

    def _on_move_up(self) -> None:
        """Move the selected path up in the list."""
        sel = self.listbox.curselection()
        if not sel or sel[0] == 0 or not self.current_tab_name:
            return
        idx = sel[0]
        self.config.move_path_in_group(self.current_tab_name, idx, idx - 1)
        self.config.save()
        self._refresh_listbox()
        self.listbox.selection_set(idx - 1)
        log.debug("Path moved up: [%d] -> [%d] in '%s'", idx, idx - 1, self.current_tab_name)

    def _on_move_down(self) -> None:
        """Move the selected path down in the list."""
        sel = self.listbox.curselection()
        if not sel or not self.current_tab_name:
            return
        idx = sel[0]
        group = self.config.get_tab_group(self.current_tab_name)
        if group and idx < len(group.paths) - 1:
            self.config.move_path_in_group(self.current_tab_name, idx, idx + 1)
            self.config.save()
            self._refresh_listbox()
            self.listbox.selection_set(idx + 1)
            log.debug("Path moved down: [%d] -> [%d] in '%s'", idx, idx + 1, self.current_tab_name)

    def _on_browse(self) -> None:
        """Open a folder selection dialog."""
        top = self.frame.winfo_toplevel()
        path = filedialog.askdirectory(parent=top)
        if path:
            normalized = os.path.normpath(path)
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, normalized)

    def _on_listbox_select(self, _event: Any) -> None:
        """Copy selected listbox path to the path entry field."""
        sel = self.listbox.curselection()
        if not sel:
            return
        path = self.listbox.get(sel[0])
        self.path_entry.delete(0, tk.END)
        self.path_entry.insert(0, path)

    def _on_get_finder_bounds(self) -> None:
        """Get the frontmost Finder window's bounds and fill geometry fields."""
        try:
            result = subprocess.run(
                ["osascript", "-e",
                 'tell application "Finder" to get bounds of front Finder window'],
                capture_output=True, text=True, timeout=5,
            )
            if result.returncode != 0:
                messagebox.showinfo(
                    t("window.no_finder_title"),
                    t("window.no_finder_msg"),
                    parent=self.frame.winfo_toplevel(),
                )
                return
            parts = [int(s.strip()) for s in result.stdout.strip().split(",")]
            x, y, x2, y2 = parts[0], parts[1], parts[2], parts[3]
            w, h = x2 - x, y2 - y
        except Exception as e:
            log.warning("Failed to get Finder bounds: %s", e)
            messagebox.showinfo(
                t("window.no_finder_title"),
                t("window.no_finder_msg"),
                parent=self.frame.winfo_toplevel(),
            )
            return

        for entry, val in [
            (self._geom_x_entry, x), (self._geom_y_entry, y),
            (self._geom_w_entry, w), (self._geom_h_entry, h),
        ]:
            entry.delete(0, tk.END)
            entry.insert(0, str(val))
        self._save_geometry()

    def _on_get_explorer_bounds(self) -> None:
        """Get the frontmost Explorer window's bounds and fill geometry fields."""
        try:
            from file_tab_opener.opener_win import get_frontmost_explorer_rect

            rect = get_frontmost_explorer_rect()
            if rect is None:
                messagebox.showinfo(
                    t("window.no_explorer_title"),
                    t("window.no_explorer_msg"),
                    parent=self.frame.winfo_toplevel(),
                )
                return
            x, y, w, h = rect
        except Exception as e:
            log.warning("Failed to get Explorer bounds: %s", e)
            messagebox.showinfo(
                t("window.no_explorer_title"),
                t("window.no_explorer_msg"),
                parent=self.frame.winfo_toplevel(),
            )
            return

        for entry, val in [
            (self._geom_x_entry, x), (self._geom_y_entry, y),
            (self._geom_w_entry, w), (self._geom_h_entry, h),
        ]:
            entry.delete(0, tk.END)
            entry.insert(0, str(val))
        self._save_geometry()

    def _load_geometry(self) -> None:
        """Load window geometry values from the current tab group into the entry fields."""
        for entry in (self._geom_x_entry, self._geom_y_entry,
                       self._geom_w_entry, self._geom_h_entry):
            entry.delete(0, tk.END)
        if not self.current_tab_name:
            return
        group = self.config.get_tab_group(self.current_tab_name)
        if not group:
            return
        if group.window_x is not None:
            self._geom_x_entry.insert(0, str(group.window_x))
        if group.window_y is not None:
            self._geom_y_entry.insert(0, str(group.window_y))
        if group.window_width is not None:
            self._geom_w_entry.insert(0, str(group.window_width))
        if group.window_height is not None:
            self._geom_h_entry.insert(0, str(group.window_height))

    def _save_geometry(self) -> None:
        """Save window geometry values from the entry fields to the current tab group.

        Clamps width and height to minimum values.
        """
        if not self.current_tab_name:
            return
        group = self.config.get_tab_group(self.current_tab_name)
        if not group:
            return
        group.window_x = self._parse_int(self._geom_x_entry.get())
        group.window_y = self._parse_int(self._geom_y_entry.get())
        group.window_width = self._clamp_min(
            self._parse_int(self._geom_w_entry.get()), MIN_WINDOW_WIDTH
        )
        group.window_height = self._clamp_min(
            self._parse_int(self._geom_h_entry.get()), MIN_WINDOW_HEIGHT
        )
        # Update entry fields to show clamped values
        self._update_entry(self._geom_w_entry, group.window_width)
        self._update_entry(self._geom_h_entry, group.window_height)
        self.config.save()

    @staticmethod
    def _parse_int(value: str) -> int | None:
        """Parse an integer from a string. Returns None if invalid or empty."""
        try:
            return int(value.strip())
        except (ValueError, TypeError):
            return None

    @staticmethod
    def _clamp_min(value: int | None, minimum: int) -> int | None:
        """Clamp a value to a minimum. Returns None if value is None."""
        if value is None:
            return None
        return max(value, minimum)

    @staticmethod
    def _update_entry(entry: Any, value: int | None) -> None:
        """Update an entry widget's text without triggering extra events."""
        current = entry.get().strip()
        new_text = str(value) if value is not None else ""
        if current != new_text:
            entry.delete(0, tk.END)
            if new_text:
                entry.insert(0, new_text)

    def _get_window_rect(self) -> tuple[int, int, int, int] | None:
        """Return the window rect for the current tab group, or None if incomplete."""
        self._save_geometry()
        if not self.current_tab_name:
            return None
        group = self.config.get_tab_group(self.current_tab_name)
        if not group:
            return None
        if (group.window_x is not None and group.window_y is not None
                and group.window_width is not None and group.window_height is not None):
            return (group.window_x, group.window_y, group.window_width, group.window_height)
        return None

    def _on_open_as_tabs(self) -> None:
        """Handle the Open as Tabs button click."""
        if self._opening:
            return
        top = self.frame.winfo_toplevel()
        if not self.current_tab_name:
            messagebox.showinfo(
                t("tab.no_tab_title"), t("tab.no_tab_msg"), parent=top
            )
            return
        group = self.config.get_tab_group(self.current_tab_name)
        if not group or not group.paths:
            messagebox.showinfo(
                t("tab.no_paths_title"), t("tab.no_paths_msg"), parent=top
            )
            return
        self._opening = True
        log.info("Opening as tabs: tab='%s', %d paths", self.current_tab_name, len(group.paths))
        self.on_open_tabs(group.paths, self._get_window_rect())

    def reset_opening(self) -> None:
        """Reset the opening flag. Called by MainWindow when the worker thread completes."""
        self._opening = False
