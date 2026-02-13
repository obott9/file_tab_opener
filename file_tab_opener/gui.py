"""
GUI module for File Tab Opener.

Supports customtkinter (modern UI) with fallback to standard tkinter.
All user-facing text is provided via the i18n module.
"""

from __future__ import annotations

import os
import threading
import tkinter as tk
import tkinter.ttk as ttk
from collections.abc import Callable
from pathlib import Path
from tkinter import filedialog, messagebox, simpledialog
from typing import Any

from file_tab_opener.config import ConfigManager
from file_tab_opener import i18n
from file_tab_opener.i18n import t, SUPPORTED_LANGS, LANG_NAMES

# --- customtkinter availability check ---
try:
    import customtkinter as ctk

    CTK_AVAILABLE = True
except ImportError:
    CTK_AVAILABLE = False


# ============================================================
# Widget abstraction (factory functions)
# ============================================================


def get_root(title: str = "File Tab Opener") -> tk.Tk:
    """Create the root window."""
    if CTK_AVAILABLE:
        ctk.set_appearance_mode("system")
        ctk.set_default_color_theme("blue")
        root = ctk.CTk()
    else:
        root = tk.Tk()
    root.title(title)
    return root


def Frame(parent: Any, **kw: Any) -> ttk.Frame:
    """Create a frame widget."""
    if CTK_AVAILABLE:
        return ctk.CTkFrame(parent, **kw)
    return ttk.Frame(parent, **kw)


def Button(parent: Any, text: str = "", command: Callable[[], None] | None = None, **kw: Any) -> ttk.Button:
    """Create a button widget."""
    if CTK_AVAILABLE:
        return ctk.CTkButton(parent, text=text, command=command, **kw)
    return ttk.Button(parent, text=text, command=command, **kw)


def Label(parent: Any, text: str = "", **kw: Any) -> ttk.Label:
    """Create a label widget."""
    if CTK_AVAILABLE:
        return ctk.CTkLabel(parent, text=text, **kw)
    return ttk.Label(parent, text=text, **kw)


def Entry(parent: Any, **kw: Any) -> ttk.Entry:
    """Create an entry widget."""
    if CTK_AVAILABLE:
        return ctk.CTkEntry(parent, **kw)
    return ttk.Entry(parent, **kw)


# ============================================================
# TabView abstraction class
# ============================================================


class TabView:
    """Tab name selector using segmented button (CTk) or button row (ttk).

    This is a lightweight tab-name-only selector — no content area.
    The associated content (listbox, etc.) is managed externally.
    """

    def __init__(self, parent: Any, on_tab_changed: Callable[[str], None] | None = None) -> None:
        self._names: list[str] = []
        self._current: str | None = None
        self._on_tab_changed = on_tab_changed
        self._parent = parent

        self._frame = ttk.Frame(parent)
        self._seg_widget: Any = None  # CTkSegmentedButton or None
        self._buttons: dict[str, Any] = {}  # ttk fallback buttons

    def pack(self, **kw: Any) -> None:
        """Pack the tab selector."""
        self._frame.pack(**kw)

    def grid(self, **kw: Any) -> None:
        """Grid the tab selector."""
        self._frame.grid(**kw)

    def add_tab(self, name: str) -> None:
        """Add a tab name."""
        if name in self._names:
            return
        self._names.append(name)
        self._rebuild()

    def delete_tab(self, name: str) -> None:
        """Delete a tab by name."""
        if name not in self._names:
            return
        self._names.remove(name)
        if self._current == name:
            self._current = self._names[0] if self._names else None
        self._rebuild()

    def get_current_tab_name(self) -> str | None:
        """Return the name of the currently selected tab."""
        return self._current

    def set_current_tab(self, name: str) -> None:
        """Select a tab by name."""
        if name not in self._names:
            return
        self._current = name
        self._update_selection()

    def tab_names(self) -> list[str]:
        """Return the list of tab names."""
        return list(self._names)

    def _rebuild(self) -> None:
        """Rebuild the selector widget from scratch."""
        # Clear existing children
        for child in self._frame.winfo_children():
            child.destroy()
        self._seg_widget = None
        self._buttons.clear()

        if not self._names:
            return

        if CTK_AVAILABLE:
            self._seg_widget = ctk.CTkSegmentedButton(
                self._frame,
                values=self._names,
                command=self._on_seg_click,
            )
            self._seg_widget.pack(fill=tk.X)
            if self._current and self._current in self._names:
                self._seg_widget.set(self._current)
            elif self._names:
                self._current = self._names[0]
                self._seg_widget.set(self._current)
        else:
            for name in self._names:
                btn = ttk.Button(
                    self._frame,
                    text=name,
                    command=lambda n=name: self._on_btn_click(n),
                )
                btn.pack(side=tk.LEFT, padx=1)
                self._buttons[name] = btn
            if not self._current or self._current not in self._names:
                self._current = self._names[0]
            self._update_ttk_highlight()

    def _update_selection(self) -> None:
        """Update the visual selection state."""
        if CTK_AVAILABLE and self._seg_widget:
            if self._current:
                self._seg_widget.set(self._current)
        else:
            self._update_ttk_highlight()

    def _update_ttk_highlight(self) -> None:
        """Highlight the active tab button (ttk fallback)."""
        for name, btn in self._buttons.items():
            if name == self._current:
                btn.state(["pressed"])
            else:
                btn.state(["!pressed"])

    def _on_seg_click(self, value: str) -> None:
        """Handle CTkSegmentedButton click."""
        self._current = value
        if self._on_tab_changed:
            self._on_tab_changed(value)

    def _on_btn_click(self, name: str) -> None:
        """Handle ttk button click."""
        self._current = name
        self._update_ttk_highlight()
        if self._on_tab_changed:
            self._on_tab_changed(name)


# ============================================================
# Section 1: History combobox
# ============================================================


class HistorySection:
    """Top section: history dropdown + Open / Pin / Clear buttons."""

    def __init__(
        self,
        parent: Any,
        config: ConfigManager,
        on_open_folder: Callable[[str], None],
    ) -> None:
        self.config = config
        self.on_open_folder = on_open_folder
        self._parent = parent

        self.frame = Frame(parent)
        self._build_widgets()
        self._refresh_combobox()

    def _build_widgets(self) -> None:
        """Build all widgets in the history section."""
        Label(self.frame, text=t("history.label")).pack(side=tk.LEFT, padx=(0, 5))

        # Combobox (always use ttk.Combobox)
        self.combobox = ttk.Combobox(self.frame, width=50)
        self.combobox.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        Button(self.frame, text=t("history.open"), command=self._on_open, width=6).pack(
            side=tk.LEFT, padx=2
        )
        Button(self.frame, text=t("history.pin"), command=self._on_pin, width=5).pack(
            side=tk.LEFT, padx=2
        )
        Button(self.frame, text=t("history.clear"), command=self._on_clear, width=6).pack(
            side=tk.LEFT, padx=2
        )

    def _refresh_combobox(self) -> None:
        """Update combobox values from history."""
        history = self.config.get_sorted_history()
        values: list[str] = []
        for entry in history:
            prefix = "[*] " if entry.pinned else "    "
            values.append(f"{prefix}{entry.path}")
        self.combobox["values"] = values

    def _get_selected_path(self) -> str:
        """Extract the path from combobox text (strip prefix and surrounding double quotes)."""
        text = self.combobox.get().strip()
        if text.startswith("[*] "):
            text = text[4:]
        elif text.startswith("    "):
            text = text[4:]
        # Strip surrounding double quotes from Explorer's "Copy path"
        if text.startswith('"') and text.endswith('"') and len(text) >= 2:
            text = text[1:-1]
        return text

    def _on_open(self) -> None:
        """Handle the Open button click."""
        path = self._get_selected_path()
        if not path:
            return
        expanded = os.path.expanduser(path)
        if Path(expanded).is_dir():
            self.config.add_history(expanded)
            self.config.save()
            self._refresh_combobox()
            # Update displayed text to the resolved path (without quotes)
            self.combobox.set(expanded)
            self.on_open_folder(expanded)
        else:
            messagebox.showwarning(
                t("history.invalid_path_title"),
                t("history.invalid_path_msg", path=path),
                parent=self.frame.winfo_toplevel(),
            )

    def _on_pin(self) -> None:
        """Handle the Pin button click."""
        path = self._get_selected_path()
        if not path:
            return
        expanded = os.path.expanduser(path)
        # Add to history if not already present
        normalized = os.path.normpath(expanded)
        found = False
        for entry in self.config.data.history:
            if os.path.normpath(entry.path) == normalized:
                found = True
                break
        if not found:
            self.config.add_history(expanded)
        self.config.toggle_pin(expanded)
        self.config.save()
        self._refresh_combobox()

    def _on_clear(self) -> None:
        """Handle the Clear button click."""
        result = messagebox.askyesno(
            t("history.clear_confirm_title"),
            t("history.clear_confirm_msg"),
            parent=self.frame.winfo_toplevel(),
        )
        if result:
            self.config.clear_history(keep_pinned=True)
            self.config.save()
            self._refresh_combobox()


# ============================================================
# Section 2: Tab group with listbox
# ============================================================


class TabGroupSection:
    """Bottom section: tab bar + path list + action buttons + Open as Tabs button."""

    def __init__(
        self,
        parent: Any,
        config: ConfigManager,
        on_open_tabs: Callable[[list[str]], None],
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

        # --- Tab view (tab names only, no expand) ---
        self.tab_view = TabView(self.frame, on_tab_changed=self._on_tab_changed)
        self.tab_view.pack(fill=tk.X)

        # --- Content area (listbox + buttons) ---
        content = Frame(self.frame)
        content.pack(fill=tk.BOTH, expand=True, pady=5)

        # Listbox (left side)
        list_frame = ttk.Frame(content)
        list_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        self.listbox = tk.Listbox(list_frame, selectmode=tk.SINGLE, height=10)
        scrollbar = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self.listbox.yview
        )
        self.listbox.configure(yscrollcommand=scrollbar.set)
        self.listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

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
            except Exception:
                pass

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

        self.path_entry = Entry(entry_frame)
        self.path_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        # Enter key to add path
        self.path_entry.bind("<Return>", lambda e: self._on_add_path())

        # --- Open as Tabs button ---
        self.open_btn = Button(
            self.frame, text=t("tab.open_as_tabs"), command=self._on_open_as_tabs
        )
        self.open_btn.pack(fill=tk.X, pady=(5, 0), ipady=8)

    def _load_tabs_from_config(self) -> None:
        """Restore tab groups from the config file."""
        for group in self.config.data.tab_groups:
            self.tab_view.add_tab(group.name)
        names = self.tab_view.tab_names()
        if names:
            self.tab_view.set_current_tab(names[0])
            self.current_tab_name = names[0]
            self._refresh_listbox()

    def _on_tab_changed(self, tab_name: str) -> None:
        """Handle tab selection change."""
        self.current_tab_name = tab_name
        self._refresh_listbox()

    def _refresh_listbox(self) -> None:
        """Update the listbox with paths from the current tab group."""
        self.listbox.delete(0, tk.END)
        if not self.current_tab_name:
            return
        group = self.config.get_tab_group(self.current_tab_name)
        if group:
            for path in group.paths:
                self.listbox.insert(tk.END, path)

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
            self.config.delete_tab_group(name)
            self.config.save()
            self.tab_view.delete_tab(name)
            remaining = self.tab_view.tab_names()
            if remaining:
                self.tab_view.set_current_tab(remaining[0])
                self.current_tab_name = remaining[0]
            else:
                self.current_tab_name = None
            self._refresh_listbox()

    def _on_add_path(self) -> None:
        """Handle the Add Path button click or Enter key in path entry."""
        path = self.path_entry.get().strip()
        if path.startswith('"') and path.endswith('"') and len(path) >= 2:
            path = path[1:-1]
        if not path:
            return
        top = self.frame.winfo_toplevel()
        if not self.current_tab_name:
            messagebox.showinfo(
                t("tab.no_tab_title"), t("tab.no_tab_msg"), parent=top
            )
            return
        expanded = os.path.expanduser(path)
        if not Path(expanded).is_dir():
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

    def _on_remove_path(self) -> None:
        """Handle the Remove Path button click."""
        sel = self.listbox.curselection()
        if not sel or not self.current_tab_name:
            return
        self.config.remove_path_from_group(self.current_tab_name, sel[0])
        self.config.save()
        self._refresh_listbox()

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

    def _on_browse(self) -> None:
        """Open a folder selection dialog."""
        top = self.frame.winfo_toplevel()
        path = filedialog.askdirectory(parent=top)
        if path:
            normalized = os.path.normpath(path)
            self.path_entry.delete(0, tk.END)
            self.path_entry.insert(0, normalized)

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
        self.on_open_tabs(group.paths)
        # Delay flag reset to prevent double-clicks
        self.frame.after(2000, self._reset_opening_flag)

    def _reset_opening_flag(self) -> None:
        """Reset the opening flag after a delay."""
        self._opening = False


# ============================================================
# Main window
# ============================================================


class MainWindow:
    """Application main window."""

    def __init__(self, config: ConfigManager, opener: Any) -> None:
        self.config = config
        self.opener = opener
        self.root = get_root(t("app.title"))
        self._content_frame: tk.Frame | None = None

    def build(self) -> None:
        """Build the GUI layout."""
        # Restore window geometry
        geom = self.config.data.window_geometry
        if geom:
            self.root.geometry(geom)
        self.root.minsize(600, 400)

        self._build_content()

        # Window close handler
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)

    def _build_content(self) -> None:
        """Build (or rebuild) all content widgets."""
        # Destroy old content if rebuilding
        if self._content_frame is not None:
            self._content_frame.destroy()

        self._content_frame = ttk.Frame(self.root)
        self._content_frame.pack(fill=tk.BOTH, expand=True)

        # --- Settings bar (top-right): timeout + language ---
        settings_bar = Frame(self._content_frame)
        settings_bar.pack(fill=tk.X, padx=10, pady=(5, 0))

        settings_inner = ttk.Frame(settings_bar)
        settings_inner.pack(side=tk.RIGHT)

        # Timeout selector
        Label(settings_inner, text=t("settings.timeout")).pack(side=tk.LEFT, padx=(0, 3))
        self._timeout_combo = ttk.Combobox(
            settings_inner,
            values=["5", "10", "15", "30", "60"],
            state="readonly",
            width=3,
        )
        saved_timeout = self.config.data.settings.get("timeout", 30)
        self._timeout_combo.set(str(saved_timeout))
        self._timeout_combo.pack(side=tk.LEFT)
        self._timeout_combo.bind("<<ComboboxSelected>>", self._on_timeout_changed)
        Label(settings_inner, text=t("settings.timeout_unit")).pack(
            side=tk.LEFT, padx=(1, 10)
        )

        # Language selector
        Label(settings_inner, text="🌐").pack(side=tk.LEFT, padx=(0, 3))
        self._lang_combo = ttk.Combobox(
            settings_inner,
            values=[LANG_NAMES[code] for code in SUPPORTED_LANGS],
            state="readonly",
            width=10,
        )
        current = i18n.get_language()
        if current in LANG_NAMES:
            self._lang_combo.set(LANG_NAMES[current])
        self._lang_combo.pack(side=tk.LEFT)
        self._lang_combo.bind("<<ComboboxSelected>>", self._on_language_changed)

        # --- Section 1: History ---
        self.history_section = HistorySection(
            self._content_frame, self.config, on_open_folder=self._open_single_folder
        )
        self.history_section.frame.pack(fill=tk.X, padx=10, pady=(5, 5))

        # Separator
        ttk.Separator(self._content_frame, orient=tk.HORIZONTAL).pack(
            fill=tk.X, padx=10, pady=5
        )

        # --- Section 2: Tab groups ---
        self.tab_group_section = TabGroupSection(
            self._content_frame, self.config, on_open_tabs=self._open_folders_as_tabs
        )
        self.tab_group_section.frame.pack(
            fill=tk.BOTH, expand=True, padx=10, pady=(5, 10)
        )

    def _on_timeout_changed(self, event: Any) -> None:
        """Handle timeout change from the combobox."""
        try:
            value = int(self._timeout_combo.get())
        except ValueError:
            return
        self.config.data.settings["timeout"] = value
        self.config.save()

    def _on_language_changed(self, event: Any) -> None:
        """Handle language switch from the combobox."""
        selected_name = self._lang_combo.get()
        for code, name in LANG_NAMES.items():
            if name == selected_name:
                if code != i18n.get_language():
                    i18n.set_language(code)
                    self.config.data.settings["language"] = code
                    self.config.save()
                    self.root.title(t("app.title"))
                    self._build_content()
                return

    def _get_timeout(self) -> float:
        """Get the current timeout setting in seconds."""
        val = self.config.data.settings.get("timeout", 30)
        try:
            return float(val)
        except (TypeError, ValueError):
            return 30.0

    def _open_single_folder(self, path: str) -> None:
        """Open a single folder."""
        self.opener.open_single_folder(path)

    def _open_folders_as_tabs(self, paths: list[str]) -> None:
        """Open multiple folders as tabs (runs in a worker thread)."""
        valid, invalid = self.opener.validate_paths(paths)
        if invalid:
            messagebox.showwarning(
                t("error.invalid_paths_title"),
                t("error.invalid_paths_msg", paths="\n".join(invalid)),
                parent=self.root,
            )
        if not valid:
            return

        timeout = self._get_timeout()

        def do_open() -> None:
            self.opener.open_folders_as_tabs(
                valid,
                on_error=lambda p, e: self.root.after(
                    0,
                    lambda: messagebox.showerror(
                        t("error.title"),
                        t("error.open_failed", path=p, error=e),
                        parent=self.root,
                    ),
                ),
                timeout=timeout,
            )

        threading.Thread(target=do_open, daemon=True).start()

    def _on_close(self) -> None:
        """Save window geometry and close."""
        self.config.data.window_geometry = self.root.geometry()
        self.config.save()
        self.root.destroy()

    def run(self) -> None:
        """Start the main loop."""
        self.root.mainloop()
