"""
Main window for File Tab Opener GUI.

Composes HistorySection and TabGroupSection into the application window.
"""

from __future__ import annotations

import threading
import tkinter as tk
import tkinter.ttk as ttk
from tkinter import messagebox
from typing import Any

from file_tab_opener.config import ConfigManager
from file_tab_opener import i18n
from file_tab_opener.i18n import t, SUPPORTED_LANGS, LANG_NAMES
from file_tab_opener.widgets import Frame, Label, get_root
from file_tab_opener.history import HistorySection
from file_tab_opener.tab_group import TabGroupSection


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
        # Save current tab selection before rebuilding
        saved_tab_name: str | None = None
        if self._content_frame is not None and hasattr(self, "tab_group_section"):
            saved_tab_name = self.tab_group_section.current_tab_name

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

        # Restore tab selection after rebuild (C-1)
        if saved_tab_name:
            names = self.tab_group_section.tab_view.tab_names()
            if saved_tab_name in names:
                self.tab_group_section.tab_view.set_current_tab(saved_tab_name)
                self.tab_group_section.current_tab_name = saved_tab_name
                self.tab_group_section.restore_tab_state()

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
        idx = self._lang_combo.current()
        if idx < 0 or idx >= len(SUPPORTED_LANGS):
            return
        code = SUPPORTED_LANGS[idx]
        if code != i18n.get_language():
            i18n.set_language(code)
            self.config.data.settings["language"] = code
            self.config.save()
            self.root.title(t("app.title"))
            self._build_content()

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

    def _open_folders_as_tabs(
        self, paths: list[str], window_rect: tuple[int, int, int, int] | None = None,
    ) -> None:
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

        # Show wait cursor while tabs are being opened
        self.root.config(cursor="wait")

        def safe_after(callback: Any) -> None:
            """Schedule callback on main thread, ignoring TclError if window closed."""
            try:
                self.root.after(0, callback)
            except tk.TclError:
                pass

        def do_open() -> None:
            try:
                self.opener.open_folders_as_tabs(
                    valid,
                    on_error=lambda p, e: safe_after(
                        lambda: messagebox.showerror(
                            t("error.title"),
                            t("error.open_failed", path=p, error=e),
                            parent=self.root,
                        ),
                    ),
                    timeout=timeout,
                    window_rect=window_rect,
                )
            except Exception as e:
                safe_after(
                    lambda: messagebox.showerror(
                        t("error.title"),
                        str(e),
                        parent=self.root,
                    ),
                )
            finally:
                safe_after(self._reset_tab_opening_flag)

        threading.Thread(target=do_open, daemon=True).start()

    def _reset_tab_opening_flag(self) -> None:
        """Reset the tab group section's opening flag and cursor from the main thread."""
        if hasattr(self, "tab_group_section"):
            self.tab_group_section._opening = False
        self.root.config(cursor="")

    def _on_close(self) -> None:
        """Save window geometry and close."""
        self.config.data.window_geometry = self.root.geometry()
        self.config.save()
        self.root.destroy()

    def run(self) -> None:
        """Start the main loop."""
        self.root.mainloop()
