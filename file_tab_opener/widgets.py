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
    """Tab name selector with auto-wrapping rows (up to MAX_ROWS).

    Buttons wrap to the next row when they exceed the available width.
    Works with both customtkinter (CTkButton) and standard ttk (ttk.Button).
    """

    MAX_ROWS = 4
    _BTN_PAD_X = 2  # horizontal padding between buttons
    _BTN_PAD_Y = 1  # vertical padding between rows

    def __init__(self, parent: Any, on_tab_changed: Callable[[str], None] | None = None) -> None:
        self._names: list[str] = []
        self._current: str | None = None
        self._on_tab_changed = on_tab_changed
        self._parent = parent

        self._frame = ttk.Frame(parent)
        self._row_frames: list[Any] = []
        self._buttons: dict[str, Any] = {}
        self._last_width: int = 0
        self._relayout_pending: bool = False

        self._frame.bind("<Configure>", self._on_configure)

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

    # ---- internal ----

    def _rebuild(self) -> None:
        """Create button widgets (un-placed) and schedule layout."""
        self._clear()

        if not self._names:
            return

        if not self._current or self._current not in self._names:
            self._current = self._names[0]

        for name in self._names:
            btn = self._make_button(name)
            self._buttons[name] = btn

        self._update_selection()
        # Schedule layout after geometry is settled
        self._frame.after_idle(self._relayout)

    def _make_button(self, name: str) -> Any:
        """Create a tab button (CTkButton or ttk.Button), not yet packed."""
        if CTK_AVAILABLE:
            btn = ctk.CTkButton(
                self._frame,
                text=name,
                command=lambda n=name: self._on_btn_click(n),
            )
        else:
            btn = ttk.Button(
                self._frame,
                text=name,
                command=lambda n=name: self._on_btn_click(n),
            )
        return btn

    def _clear(self) -> None:
        """Destroy all child widgets."""
        for child in self._frame.winfo_children():
            child.destroy()
        self._row_frames.clear()
        self._buttons.clear()

    def _on_configure(self, _event: Any) -> None:
        """Handle frame resize -- re-layout if width changed."""
        new_width = self._frame.winfo_width()
        if new_width != self._last_width and new_width > 1 and self._names:
            self._last_width = new_width
            if not self._relayout_pending:
                self._relayout_pending = True
                self._frame.after_idle(self._relayout)

    def _relayout(self) -> None:
        """Place buttons into wrapping rows based on current frame width."""
        self._relayout_pending = False

        if not self._buttons:
            return

        # Remove row frames but keep button widgets alive
        for rf in self._row_frames:
            rf.destroy()
        self._row_frames.clear()

        # Unpack buttons (they are children of self._frame, not row_frames)
        for btn in self._buttons.values():
            btn.pack_forget()

        available = self._frame.winfo_width()
        if available <= 1:
            # Frame not yet mapped -- fall back to single row
            available = 10_000

        # Measure each button's required width
        btn_widths: list[tuple[str, int]] = []
        for name in self._names:
            btn = self._buttons[name]
            btn.update_idletasks()
            w = btn.winfo_reqwidth()
            if w <= 1:
                # Not yet rendered: estimate from text length
                w = max(len(name) * 9 + 20, 60)
            btn_widths.append((name, w))

        # Split names into rows (greedy, max MAX_ROWS)
        rows: list[list[str]] = []
        current_row: list[str] = []
        row_used = 0

        for name, w in btn_widths:
            needed = w + self._BTN_PAD_X * 2
            if current_row and row_used + needed > available and len(rows) < self.MAX_ROWS - 1:
                rows.append(current_row)
                current_row = []
                row_used = 0
            current_row.append(name)
            row_used += needed

        if current_row:
            rows.append(current_row)

        # If too many rows, merge excess into the last allowed row
        while len(rows) > self.MAX_ROWS:
            overflow = rows.pop()
            rows[-1].extend(overflow)

        # Pack buttons into row frames
        for row_names in rows:
            rf = ttk.Frame(self._frame)
            rf.pack(fill=tk.X, pady=self._BTN_PAD_Y)
            self._row_frames.append(rf)

            for name in row_names:
                btn = self._buttons[name]
                # Re-parent to row frame
                btn.configure(cursor="hand2") if CTK_AVAILABLE else None
                btn.pack_forget()
                btn.pack(in_=rf, side=tk.LEFT, padx=self._BTN_PAD_X, pady=0)

        self._update_selection()

    def _update_selection(self) -> None:
        """Update the visual selection state of all buttons."""
        if CTK_AVAILABLE:
            self._update_ctk_highlight()
        else:
            self._update_ttk_highlight()

    def _update_ctk_highlight(self) -> None:
        """Highlight the active tab button (customtkinter)."""
        for name, btn in self._buttons.items():
            if name == self._current:
                btn.configure(fg_color=("gray75", "gray25"))
            else:
                btn.configure(fg_color=("gray86", "gray17"))

    def _update_ttk_highlight(self) -> None:
        """Highlight the active tab button (ttk fallback)."""
        for name, btn in self._buttons.items():
            if name == self._current:
                btn.state(["pressed"])
            else:
                btn.state(["!pressed"])

    def _on_btn_click(self, name: str) -> None:
        """Handle button click."""
        self._current = name
        self._update_selection()
        if self._on_tab_changed:
            self._on_tab_changed(name)
