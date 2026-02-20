"""
Widget abstraction layer for File Tab Opener.

Provides factory functions and the TabView class that work with
customtkinter (modern UI) or fall back to standard tkinter/ttk.
"""

from __future__ import annotations

import platform
import tkinter as tk
import tkinter.ttk as ttk
from collections.abc import Callable
from typing import Any

IS_MAC = platform.system() == "Darwin"
IS_WIN = platform.system() == "Windows"

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


def Frame(parent: Any, **kw: Any) -> Any:
    """Create a frame widget (CTkFrame or ttk.Frame)."""
    if CTK_AVAILABLE:
        return ctk.CTkFrame(parent, **kw)
    return ttk.Frame(parent, **kw)


def Button(parent: Any, text: str = "", command: Callable[[], None] | None = None, **kw: Any) -> Any:
    """Create a button widget (CTkButton or ttk.Button)."""
    if CTK_AVAILABLE:
        return ctk.CTkButton(parent, text=text, command=command, **kw)
    return ttk.Button(parent, text=text, command=command, **kw)


def Label(parent: Any, text: str = "", **kw: Any) -> Any:
    """Create a label widget (CTkLabel or ttk.Label)."""
    if CTK_AVAILABLE:
        return ctk.CTkLabel(parent, text=text, **kw)
    return ttk.Label(parent, text=text, **kw)


def Entry(parent: Any, **kw: Any) -> Any:
    """Create an entry widget (CTkEntry or ttk.Entry)."""
    if CTK_AVAILABLE:
        return ctk.CTkEntry(parent, **kw)
    return ttk.Entry(parent, **kw)


# ============================================================
# Helper functions
# ============================================================


def _strip_quotes(text: str) -> str:
    """Strip matching surrounding quotes (shell quoting artifacts).

    Delegates to config.strip_quotes (single source of truth).
    """
    from file_tab_opener.config import strip_quotes
    return strip_quotes(text)


def _setup_placeholder(entry: ttk.Entry, placeholder: str) -> None:
    """Add placeholder text to a ttk.Entry (grey hint when empty)."""
    def _on_focus_in(_event: Any) -> None:
        if entry.get() == placeholder:
            entry.delete(0, tk.END)
            entry.configure(foreground="")

    def _on_focus_out(_event: Any) -> None:
        if not entry.get():
            entry.insert(0, placeholder)
            entry.configure(foreground="grey")

    entry.insert(0, placeholder)
    entry.configure(foreground="grey")
    entry.bind("<FocusIn>", _on_focus_in, add="+")
    entry.bind("<FocusOut>", _on_focus_out, add="+")


# ============================================================
# TabView abstraction class
# ============================================================


class TabView:
    """Tab name selector using segmented button (CTk) or button row (ttk).

    This is a lightweight tab-name-only selector -- no content area.
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

    def rename_tab(self, old_name: str, new_name: str) -> None:
        """Rename a tab."""
        if old_name not in self._names or new_name in self._names:
            return
        idx = self._names.index(old_name)
        self._names[idx] = new_name
        if self._current == old_name:
            self._current = new_name
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

    def move_tab(self, old_index: int, new_index: int) -> None:
        """Move a tab from old_index to new_index."""
        if 0 <= old_index < len(self._names) and 0 <= new_index < len(self._names):
            item = self._names.pop(old_index)
            self._names.insert(new_index, item)
            self._rebuild()

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
