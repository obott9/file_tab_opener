"""
History section for File Tab Opener GUI.

Top section: history entry with custom dropdown + Open / Pin / Clear buttons.
"""

from __future__ import annotations

import logging
import os
import tkinter as tk
import tkinter.ttk as ttk
from collections.abc import Callable
from pathlib import Path
from tkinter import messagebox

from file_tab_opener import is_unc_path
from typing import Any

from file_tab_opener.config import ConfigManager
from file_tab_opener.i18n import t
from file_tab_opener.widgets import (
    CTK_AVAILABLE,
    IS_MAC,
    Frame,
    Button,
    Label,
    _strip_quotes,
    _setup_placeholder,
    _is_placeholder_active,
)

log = logging.getLogger(__name__)

# Dropdown value prefixes
_PIN_PREFIX = "\U0001f4cc "   # 📌 + space (2 chars in Python)
_UNPIN_PREFIX = "   "         # 3 spaces

# Import ctk only when available
if CTK_AVAILABLE:
    import customtkinter as ctk


class HistorySection:
    """Top section: history entry with custom dropdown + Open / Pin / Clear buttons."""

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

    def _build_widgets(self) -> None:
        """Build all widgets in the history section."""
        Label(self.frame, text=t("history.label")).pack(side=tk.LEFT, padx=(0, 5))

        # Entry with custom dropdown (cross-platform scrollable list)
        entry_frame = ttk.Frame(self.frame)
        entry_frame.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))

        if CTK_AVAILABLE:
            self.entry = ctk.CTkEntry(entry_frame, placeholder_text=t("path.placeholder"))
        else:
            self.entry = ttk.Entry(entry_frame)
            _setup_placeholder(self.entry, t("path.placeholder"))
            if IS_MAC:
                self.entry.bind(
                    "<FocusIn>", lambda e: e.widget.selection_range(0, tk.END), add="+",
                )
        self.entry.pack(side=tk.LEFT, fill=tk.X, expand=True)

        # Dropdown toggle button
        self._dropdown_btn = ttk.Button(
            entry_frame, text="\u25bc", width=2, command=self._toggle_dropdown,
        )
        self._dropdown_btn.pack(side=tk.LEFT)

        self._dropdown_win: tk.Toplevel | None = None
        self._dropdown_listbox: tk.Listbox | None = None
        self._dropdown_close_pending: bool = False

        open_key = "history.open_finder" if IS_MAC else "history.open_explorer"
        Button(self.frame, text=t(open_key), command=self._on_open).pack(
            side=tk.LEFT, padx=2
        )
        Button(self.frame, text=t("history.pin"), command=self._on_pin, width=5).pack(
            side=tk.LEFT, padx=2
        )
        Button(self.frame, text=t("history.clear"), command=self._on_clear, width=6).pack(
            side=tk.LEFT, padx=2
        )

    def _toggle_dropdown(self) -> None:
        """Show or hide the custom dropdown list."""
        if self._dropdown_win and self._dropdown_win.winfo_exists():
            self._close_dropdown()
            return
        self._show_dropdown()

    def _show_dropdown(self) -> None:
        """Show the custom scrollable dropdown below the entry."""
        values = self._get_dropdown_values()
        if not values:
            log.debug("Dropdown: no history entries to show")
            return
        log.debug("Dropdown opened: %d entries", len(values))

        self._dropdown_win = tk.Toplevel(self.frame)
        self._dropdown_win.wm_overrideredirect(True)

        # Position below the entry
        x = self.entry.winfo_rootx()
        y = self.entry.winfo_rooty() + self.entry.winfo_height()
        width = self.entry.winfo_width() + self._dropdown_btn.winfo_width()

        # Calculate needed height (max 10 items)
        row_count = min(len(values), 10)

        # Background: match mode for dark/light
        bg_color = "#ffffff"
        if CTK_AVAILABLE:
            try:
                mode = ctk.get_appearance_mode()
                if mode == "Dark":
                    bg_color = "#2b2b2b"
            except Exception as e:
                log.debug("Theme detection failed: %s", e)
        self._dropdown_win.configure(bg=bg_color)

        list_frame = ttk.Frame(self._dropdown_win)
        list_frame.pack(fill=tk.BOTH, expand=True, padx=8, pady=6)

        self._dropdown_listbox = tk.Listbox(
            list_frame, selectmode=tk.SINGLE, height=row_count,
            borderwidth=0, highlightthickness=0,
        )
        scrollbar_y = ttk.Scrollbar(
            list_frame, orient=tk.VERTICAL, command=self._dropdown_listbox.yview,
        )
        scrollbar_x = ttk.Scrollbar(
            list_frame, orient=tk.HORIZONTAL, command=self._dropdown_listbox.xview,
        )
        self._dropdown_listbox.configure(
            yscrollcommand=scrollbar_y.set, xscrollcommand=scrollbar_x.set,
        )

        scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
        scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
        self._dropdown_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        for v in values:
            self._dropdown_listbox.insert(tk.END, v)

        # Theme the listbox for customtkinter dark mode
        if CTK_AVAILABLE:
            try:
                mode = ctk.get_appearance_mode()
                if mode == "Dark":
                    self._dropdown_listbox.configure(
                        bg="#2b2b2b", fg="#ffffff", selectbackground="#1f6aa5",
                    )
            except Exception as e:
                log.debug("Theme detection failed for listbox: %s", e)

        self._dropdown_listbox.bind("<<ListboxSelect>>", self._on_dropdown_select)

        # Size and position: measure actual listbox height for HiDPI support
        self._dropdown_win.update_idletasks()
        list_h = self._dropdown_listbox.winfo_reqheight()
        # Account for padding (8+8 horizontal, 6+6 vertical) and scrollbar
        pad_x, pad_y = 16, 12
        scrollbar_h = scrollbar_x.winfo_reqheight()
        total_h = list_h + scrollbar_h + pad_y
        self._dropdown_win.geometry(f"{width + pad_x}x{total_h}+{x}+{y}")

        # Close on click outside -- check listbox selection state before closing
        self._dropdown_win.bind("<FocusOut>", self._on_dropdown_focus_out)

    def _on_dropdown_focus_out(self, _event: Any) -> None:
        """Handle FocusOut on dropdown -- delay close to avoid racing with selection."""
        if self._dropdown_close_pending:
            return
        try:
            if (self._dropdown_listbox
                    and self._dropdown_listbox.winfo_exists()
                    and self._dropdown_listbox.curselection()):
                # A selection is active; let _on_dropdown_select handle it
                return
        except tk.TclError:
            pass
        self._dropdown_close_pending = True
        self.frame.after(100, self._close_dropdown)

    def _close_dropdown(self) -> None:
        """Close the custom dropdown."""
        self._dropdown_close_pending = False
        if self._dropdown_win and self._dropdown_win.winfo_exists():
            self._dropdown_win.destroy()
            log.debug("Dropdown closed")
        self._dropdown_win = None
        self._dropdown_listbox = None

    def _on_dropdown_select(self, _event: Any) -> None:
        """Handle selection from the custom dropdown."""
        if not self._dropdown_listbox:
            return
        sel = self._dropdown_listbox.curselection()
        if not sel:
            return
        value = self._dropdown_listbox.get(sel[0])
        # Strip display prefix (📌 or spaces) to get the raw path
        if value.startswith(_PIN_PREFIX):
            value = value[len(_PIN_PREFIX):]
        elif value.startswith(_UNPIN_PREFIX):
            value = value[len(_UNPIN_PREFIX):]
        self.entry.delete(0, tk.END)
        self.entry.insert(0, value)
        self._close_dropdown()

    def _get_dropdown_values(self) -> list[str]:
        """Build the dropdown value list from history."""
        history = self.config.get_sorted_history()
        values: list[str] = []
        for entry in history:
            prefix = _PIN_PREFIX if entry.pinned else _UNPIN_PREFIX
            values.append(f"{prefix}{entry.path}")
        return values

    def _get_selected_path(self) -> str:
        """Extract the raw path from entry text (strip prefix only)."""
        if _is_placeholder_active(self.entry):
            return ""
        text = self.entry.get().strip()
        if text.startswith(_PIN_PREFIX):
            text = text[len(_PIN_PREFIX):]
        elif text.startswith(_UNPIN_PREFIX):
            text = text[len(_UNPIN_PREFIX):]
        return text.strip()

    def _on_open(self) -> None:
        """Handle the Open button click."""
        path = _strip_quotes(self._get_selected_path())
        if not path:
            return
        expanded = os.path.expanduser(path)
        if is_unc_path(expanded) or Path(expanded).is_dir():
            log.info("Opening folder from history: %s", expanded)
            self.config.add_history(expanded)
            self.config.save()
            self.entry.delete(0, tk.END)
            self.entry.insert(0, expanded)
            self.on_open_folder(expanded)
        else:
            log.warning("Invalid path entered: %s", path)
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
        normalized = os.path.normpath(expanded)
        found = False
        for entry in self.config.data.history:
            if os.path.normpath(entry.path) == normalized:
                found = True
                break
        if not found:
            self.config.add_history(expanded)
        self.config.toggle_pin(normalized)
        self.config.save()
        log.info("Pin toggled for: %s", normalized)

    def _on_clear(self) -> None:
        """Handle the Clear button click."""
        result = messagebox.askyesno(
            t("history.clear_confirm_title"),
            t("history.clear_confirm_msg"),
            parent=self.frame.winfo_toplevel(),
        )
        if result:
            log.info("User confirmed history clear")
            self.config.clear_history(keep_pinned=True)
            self.config.save()
