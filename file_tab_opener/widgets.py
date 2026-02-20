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
    """Tab name selector with auto-wrapping rows and vertical scrolling.

    Buttons wrap to the next row when they exceed the available width.
    The visible area shows up to VISIBLE_ROWS rows; additional rows are
    accessible via a vertical scrollbar.
    Works with both customtkinter (CTkButton) and standard ttk (ttk.Button).
    """

    VISIBLE_ROWS = 3  # rows visible without scrolling
    _BTN_PAD_X = 2    # horizontal padding between buttons
    _BTN_PAD_Y = 1    # vertical padding between rows
    _ROW_HEIGHT = 32   # estimated pixel height per button row

    def __init__(self, parent: Any, on_tab_changed: Callable[[str], None] | None = None) -> None:
        self._names: list[str] = []
        self._current: str | None = None
        self._on_tab_changed = on_tab_changed
        self._parent = parent

        # Outer frame holds canvas + optional scrollbar
        self._frame = ttk.Frame(parent)

        self._canvas = tk.Canvas(
            self._frame, highlightthickness=0, borderwidth=0,
        )
        self._scrollbar = ttk.Scrollbar(
            self._frame, orient=tk.VERTICAL, command=self._canvas.yview,
        )
        self._canvas.configure(yscrollcommand=self._scrollbar.set)

        self._scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        self._canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        # Inner frame drawn on the canvas
        self._inner = ttk.Frame(self._canvas)
        self._canvas_window = self._canvas.create_window(
            (0, 0), window=self._inner, anchor="nw",
        )

        self._row_frames: list[Any] = []
        self._buttons: dict[str, Any] = {}
        self._last_width: int = 0
        self._relayout_pending: bool = False

        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse-wheel: bind_all on root to catch events from any child widget
        # (CTkButton has internal child widgets that swallow per-widget binds)
        self._frame.after_idle(self._setup_mousewheel)

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
        """Delete a tab by name.

        After deletion, select the right neighbor; if the deleted tab was
        the last one, select the left neighbor instead.
        """
        if name not in self._names:
            return
        idx = self._names.index(name)
        self._names.remove(name)
        if self._current == name:
            if self._names:
                # Right neighbor (same index) or left neighbor (idx-1)
                new_idx = min(idx, len(self._names) - 1)
                self._current = self._names[new_idx]
            else:
                self._current = None
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
        """Select a tab by name and scroll it into view."""
        if name not in self._names:
            return
        self._current = name
        self._update_selection()
        self._frame.after(50, self.scroll_to_current)

    def move_tab(self, old_index: int, new_index: int) -> None:
        """Move a tab from old_index to new_index."""
        if 0 <= old_index < len(self._names) and 0 <= new_index < len(self._names):
            item = self._names.pop(old_index)
            self._names.insert(new_index, item)
            self._rebuild()

    def tab_names(self) -> list[str]:
        """Return the list of tab names."""
        return list(self._names)

    def scroll_to_current(self) -> None:
        """Scroll the canvas so that the current tab's button is visible."""
        if not self._current or self._current not in self._buttons:
            return
        btn = self._buttons[self._current]
        # Get the button's y position relative to the inner frame
        try:
            btn_y = btn.winfo_y()
            btn_h = btn.winfo_height()
            inner_h = self._inner.winfo_reqheight()
            canvas_h = self._canvas.winfo_height()
            if inner_h <= canvas_h:
                return  # no scrolling needed
            # Scroll so btn top is visible, with a little margin
            top_frac = max(0, (btn_y - 2)) / inner_h
            bot_frac = min(1.0, (btn_y + btn_h + 2)) / inner_h
            vis_lo, vis_hi = self._canvas.yview()
            if top_frac < vis_lo:
                self._canvas.yview_moveto(top_frac)
            elif bot_frac > vis_hi:
                self._canvas.yview_moveto(bot_frac - (vis_hi - vis_lo))
        except Exception:
            pass

    # ---- internal ----

    def _rebuild(self) -> None:
        """Destroy everything and schedule a fresh layout."""
        self._clear_inner()

        if not self._names:
            self._update_scroll(0)
            return

        if not self._current or self._current not in self._names:
            self._current = self._names[0]

        # Measure button widths using a temporary hidden button
        self._btn_widths: list[tuple[str, int]] = []
        for name in self._names:
            w = self._estimate_btn_width(name)
            self._btn_widths.append((name, w))

        # Build the actual layout
        self._frame.after_idle(self._relayout)

    def _estimate_btn_width(self, name: str) -> int:
        """Estimate the pixel width a button would need for the given text."""
        if CTK_AVAILABLE:
            # width=0 makes CTkButton fit text; estimate with padding
            return max(len(name) * 9 + 24, 50)
        else:
            # Create a temporary button, measure, destroy
            tmp = ttk.Button(self._inner, text=name)
            tmp.update_idletasks()
            w = tmp.winfo_reqwidth()
            tmp.destroy()
            return max(w, 40)

    def _clear_inner(self) -> None:
        """Destroy all child widgets inside the inner frame."""
        for child in self._inner.winfo_children():
            child.destroy()
        self._row_frames.clear()
        self._buttons.clear()

    def _on_inner_configure(self, _event: Any) -> None:
        """Update canvas scroll region when inner frame size changes."""
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))

    def _on_canvas_configure(self, event: Any) -> None:
        """Handle canvas resize -- match inner frame width and re-layout."""
        # Keep inner frame width in sync with canvas
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

        new_width = event.width
        if new_width != self._last_width and new_width > 1 and self._names:
            self._last_width = new_width
            if not self._relayout_pending:
                self._relayout_pending = True
                self._frame.after_idle(self._relayout)

    def _setup_mousewheel(self) -> None:
        """Bind mouse-wheel to root so it works even over CTkButton internals."""
        root = self._frame.winfo_toplevel()
        root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")

    def _is_cursor_over_tabview(self, event: Any) -> bool:
        """Check if the mouse cursor is within the TabView canvas area."""
        try:
            cx = self._canvas.winfo_rootx()
            cy = self._canvas.winfo_rooty()
            cw = self._canvas.winfo_width()
            ch = self._canvas.winfo_height()
            return cx <= event.x_root <= cx + cw and cy <= event.y_root <= cy + ch
        except Exception:
            return False

    def _on_mousewheel(self, event: Any) -> None:
        """Handle mouse-wheel scroll on the tab area (bind_all handler)."""
        if not self._is_cursor_over_tabview(event):
            return
        # macOS: event.delta is ±1..N; Windows/Linux: ±120
        if IS_MAC:
            self._canvas.yview_scroll(-event.delta, "units")
        else:
            self._canvas.yview_scroll(-event.delta // 120, "units")

    def _relayout(self) -> None:
        """Destroy and recreate buttons in wrapping rows (unlimited)."""
        self._relayout_pending = False

        if not self._names:
            return

        # Destroy old rows + buttons
        self._clear_inner()

        available = self._canvas.winfo_width()
        if available <= 1:
            available = 10_000

        # Rebuild width estimates if needed
        if not hasattr(self, "_btn_widths") or len(self._btn_widths) != len(self._names):
            self._btn_widths = [
                (name, self._estimate_btn_width(name)) for name in self._names
            ]

        # Split names into rows (greedy, unlimited rows)
        rows: list[list[str]] = []
        current_row: list[str] = []
        row_used = 0

        for name, w in self._btn_widths:
            needed = w + self._BTN_PAD_X * 2
            if current_row and row_used + needed > available:
                rows.append(current_row)
                current_row = []
                row_used = 0
            current_row.append(name)
            row_used += needed

        if current_row:
            rows.append(current_row)

        # Create row frames and buttons as direct children of each row
        for row_names in rows:
            rf = ttk.Frame(self._inner)
            rf.pack(fill=tk.X, pady=self._BTN_PAD_Y)
            self._row_frames.append(rf)

            for name in row_names:
                if CTK_AVAILABLE:
                    btn = ctk.CTkButton(
                        rf, text=name,
                        width=0,  # fit to text (disable 140px default)
                        command=lambda n=name: self._on_btn_click(n),
                        cursor="hand2",
                    )
                else:
                    btn = ttk.Button(
                        rf, text=name,
                        command=lambda n=name: self._on_btn_click(n),
                    )
                btn.pack(side=tk.LEFT, padx=self._BTN_PAD_X, pady=0)
                self._buttons[name] = btn

        self._update_selection()
        self._update_scroll(len(rows))
        # Scroll to current after layout settles (after_idle is too early)
        self._frame.after(50, self.scroll_to_current)

    def _update_scroll(self, num_rows: int) -> None:
        """Set canvas height based on row count. Scrollbar is always visible."""
        row_h = self._ROW_HEIGHT + self._BTN_PAD_Y * 2
        visible = min(num_rows, self.VISIBLE_ROWS)
        display_h = max(visible, 1) * row_h
        self._canvas.configure(height=display_h)

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
                # Selected: theme accent color (blue)
                btn.configure(
                    fg_color=("#3b8ed0", "#1f6aa5"),
                    text_color=("white", "white"),
                )
            else:
                # Unselected: subtle gray
                btn.configure(
                    fg_color=("gray78", "gray28"),
                    text_color=("gray20", "gray80"),
                )

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
