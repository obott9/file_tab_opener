"""
Widget abstraction layer for File Tab Opener.

Provides factory functions and the TabView class that work with
customtkinter (modern UI) or fall back to standard tkinter/ttk.
"""

from __future__ import annotations

import logging
import platform
import tkinter as tk
import tkinter.ttk as ttk
import unicodedata
from collections.abc import Callable
from typing import Any

log = logging.getLogger(__name__)

__all__ = [
    "CTK_AVAILABLE",
    "IS_MAC",
    "IS_WIN",
    "get_root",
    "Frame",
    "Button",
    "Label",
    "Entry",
    "TabView",
]

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
    """Strip matching surrounding quotes. Delegates to config.strip_quotes."""
    from file_tab_opener.config import strip_quotes
    return strip_quotes(text)


def _text_display_width(text: str) -> int:
    """Estimate display width of text, counting wide (CJK) chars as 2."""
    width = 0
    for ch in text:
        eaw = unicodedata.east_asian_width(ch)
        width += 2 if eaw in ("W", "F") else 1
    return width


def _setup_placeholder(entry: ttk.Entry, placeholder: str) -> None:
    """Add placeholder text to a ttk.Entry (grey hint when empty)."""
    entry._placeholder_active = True  # type: ignore[attr-defined]

    def _on_focus_in(_event: Any) -> None:
        if entry._placeholder_active:  # type: ignore[attr-defined]
            entry.delete(0, tk.END)
            entry.configure(foreground="")
            entry._placeholder_active = False  # type: ignore[attr-defined]

    def _on_focus_out(_event: Any) -> None:
        if not entry.get():
            entry.insert(0, placeholder)
            entry.configure(foreground="grey")
            entry._placeholder_active = True  # type: ignore[attr-defined]

    entry.insert(0, placeholder)
    entry.configure(foreground="grey")
    entry.bind("<FocusIn>", _on_focus_in, add="+")
    entry.bind("<FocusOut>", _on_focus_out, add="+")


def _is_placeholder_active(entry: Any) -> bool:
    """Check if the entry is currently showing placeholder text."""
    if CTK_AVAILABLE:
        import customtkinter as _ctk
        if isinstance(entry, _ctk.CTkEntry):
            # CTkEntry shows placeholder when _entry widget is empty
            return entry.get() == ""
    return getattr(entry, "_placeholder_active", False)


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
        self._rebuild_in_progress: bool = False
        self._scroll_needed: bool = False

        self._inner.bind("<Configure>", self._on_inner_configure)
        self._canvas.bind("<Configure>", self._on_canvas_configure)

        # Mouse-wheel / touchpad: bind_all on root to catch events from any
        # child widget (CTkButton has internal child widgets that swallow
        # per-widget binds).
        # Tk 9.0+ on macOS Aqua generates <TouchpadScroll> for trackpad
        # two-finger scrolling (TIP 684), while <MouseWheel> only fires
        # for an actual mouse wheel.  We bind both events.
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
        if self._rebuild_in_progress:
            # Layout not ready yet; _on_inner_configure will scroll later.
            self._scroll_needed = True
        else:
            self.scroll_to_current()

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
        try:
            # Force geometry to be fully calculated before reading positions
            self._frame.update_idletasks()

            # btn.winfo_y() is relative to its parent (row_frame),
            # so add the row_frame's y position within the inner frame.
            row_frame = btn.master
            btn_y = row_frame.winfo_y() + btn.winfo_y()
            btn_h = btn.winfo_height()
            inner_h = self._inner.winfo_reqheight()
            canvas_h = self._canvas.winfo_height()
            if inner_h <= canvas_h or inner_h <= 0:
                return
            top_frac = max(0.0, (btn_y - 2) / inner_h)
            bot_frac = min(1.0, (btn_y + btn_h + 2) / inner_h)
            vis_lo, vis_hi = self._canvas.yview()
            if top_frac < vis_lo:
                self._canvas.yview_moveto(top_frac)
            elif bot_frac > vis_hi:
                target = bot_frac - (vis_hi - vis_lo)
                self._canvas.yview_moveto(max(0.0, target))
        except Exception as e:
            log.debug("scroll_to_current failed: %s", e)

    # ---- internal ----

    def _rebuild(self) -> None:
        """Destroy everything and schedule a fresh layout."""
        self._rebuild_in_progress = True
        self._clear_inner()

        if not self._names:
            self._update_scroll(0)
            self._rebuild_in_progress = False
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
        """Measure the pixel width a button needs for the given text.

        Creates a temporary button, measures its requested width, then
        destroys it. Works with both CTkButton and ttk.Button.
        """
        if CTK_AVAILABLE:
            tmp = ctk.CTkButton(self._inner, text=name, width=0)
            tmp.update_idletasks()
            w = tmp.winfo_reqwidth()
            tmp.destroy()
            return max(w, 50)
        else:
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
        """Update canvas scroll region when inner frame size changes.

        This fires after the inner frame's geometry is finalized, so it
        is the right moment to scroll the current tab into view.
        """
        self._canvas.configure(scrollregion=self._canvas.bbox("all"))
        if self._scroll_needed:
            self._scroll_needed = False
            self.scroll_to_current()

    def _on_canvas_configure(self, event: Any) -> None:
        """Handle canvas resize -- match inner frame width and re-layout."""
        # Keep inner frame width in sync with canvas
        self._canvas.itemconfigure(self._canvas_window, width=event.width)

        # Suppress re-layout while a rebuild chain is active; the rebuild's
        # own _relayout call will use the correct width.
        if self._rebuild_in_progress:
            return

        new_width = event.width
        if new_width != self._last_width and new_width > 1 and self._names:
            self._last_width = new_width
            if not self._relayout_pending:
                self._relayout_pending = True
                self._frame.after_idle(self._relayout)

    def _setup_mousewheel(self) -> None:
        """Bind mouse-wheel / touchpad to root so it works over CTkButton internals.

        Tk 9.0+ on macOS Aqua sends <TouchpadScroll> for trackpad gestures
        (TIP 684) and <MouseWheel> only for an actual mouse wheel.
        We bind both events so scrolling works with either input device.
        """
        root = self._frame.winfo_toplevel()
        root.bind_all("<MouseWheel>", self._on_mousewheel, add="+")
        # Tk 9.0+ (Aqua / Windows): <TouchpadScroll> for trackpad gestures
        try:
            root.bind_all("<TouchpadScroll>", self._on_touchpad_scroll, add="+")
        except tk.TclError:
            pass  # older Tk without TouchpadScroll support

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

    def _on_touchpad_scroll(self, event: Any) -> None:
        """Handle touchpad scroll on the tab area (Tk 9.0+ TIP 684).

        On Tk 9.0+ (macOS Aqua / Windows), trackpad two-finger scrolling
        generates <TouchpadScroll> events.  The delta packs Δx (high 16 bits)
        and Δy (low 16 bits) as signed 16-bit integers.
        """
        if not self._is_cursor_over_tabview(event):
            return
        # Extract Δy from low 16 bits (signed)
        raw = event.delta
        dy = raw & 0xFFFF
        if dy >= 0x8000:
            dy -= 0x10000
        if dy != 0:
            self._canvas.yview_scroll(-dy, "units")

    def _relayout(self) -> None:
        """Destroy and recreate buttons in wrapping rows (unlimited)."""
        self._relayout_pending = False

        if not self._names:
            self._rebuild_in_progress = False
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
        # Mark rebuild complete; _on_inner_configure will scroll into view.
        self._rebuild_in_progress = False
        self._scroll_needed = True

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
