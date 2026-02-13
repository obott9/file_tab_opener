"""
Internationalization (i18n) support.

Simple dictionary-based localization. Detects system locale and provides
translated strings via the `t()` function.
"""

from __future__ import annotations

import locale
import logging
from typing import Final

log = logging.getLogger(__name__)

# Supported language codes
LANG_EN: Final[str] = "en"
LANG_JA: Final[str] = "ja"

# Display names for the language switcher UI
LANG_NAMES: Final[dict[str, str]] = {
    LANG_EN: "English",
    LANG_JA: "日本語",
}

# Ordered list of supported languages
SUPPORTED_LANGS: Final[list[str]] = [LANG_EN, LANG_JA]

# Translation table: key -> {lang: text}
_STRINGS: Final[dict[str, dict[str, str]]] = {
    # --- App ---
    "app.title": {
        "en": "File Tab Opener",
        "ja": "File Tab Opener",
    },

    # --- History section ---
    "history.label": {
        "en": "History:",
        "ja": "\u5c65\u6b74:",
    },
    "history.open": {
        "en": "Open",
        "ja": "\u958b\u304f",
    },
    "history.pin": {
        "en": "Pin",
        "ja": "Pin",
    },
    "history.clear": {
        "en": "Clear",
        "ja": "Clear",
    },
    "history.clear_confirm_title": {
        "en": "Clear History",
        "ja": "\u5c65\u6b74\u30af\u30ea\u30a2",
    },
    "history.clear_confirm_msg": {
        "en": "Delete all history except pinned items?",
        "ja": "\u30d4\u30f3\u7559\u3081\u4ee5\u5916\u306e\u5c65\u6b74\u3092\u3059\u3079\u3066\u524a\u9664\u3057\u307e\u3059\u304b\uff1f",
    },
    "history.invalid_path_title": {
        "en": "Invalid Path",
        "ja": "\u7121\u52b9\u306a\u30d1\u30b9",
    },
    "history.invalid_path_msg": {
        "en": "Folder does not exist:\n{path}",
        "ja": "\u30d5\u30a9\u30eb\u30c0\u304c\u5b58\u5728\u3057\u307e\u305b\u3093:\n{path}",
    },

    # --- Tab group section ---
    "tab.add": {
        "en": "+ Add Tab",
        "ja": "+ \u30bf\u30d6\u8ffd\u52a0",
    },
    "tab.delete": {
        "en": "x Delete Tab",
        "ja": "x \u30bf\u30d6\u524a\u9664",
    },
    "tab.add_dialog_title": {
        "en": "Add Tab",
        "ja": "\u30bf\u30d6\u8ffd\u52a0",
    },
    "tab.add_dialog_prompt": {
        "en": "Enter tab name:",
        "ja": "\u30bf\u30d6\u540d\u3092\u5165\u529b:",
    },
    "tab.duplicate_title": {
        "en": "Duplicate",
        "ja": "\u91cd\u8907",
    },
    "tab.duplicate_msg": {
        "en": "Tab '{name}' already exists.",
        "ja": "\u30bf\u30d6 '{name}' \u306f\u65e2\u306b\u5b58\u5728\u3057\u307e\u3059\u3002",
    },
    "tab.delete_confirm_title": {
        "en": "Delete Tab",
        "ja": "\u30bf\u30d6\u524a\u9664",
    },
    "tab.delete_confirm_msg": {
        "en": "Delete tab '{name}' and all its paths?",
        "ja": "\u30bf\u30d6 '{name}' \u3068\u305d\u306e\u30d1\u30b9\u3092\u3059\u3079\u3066\u524a\u9664\u3057\u307e\u3059\u304b\uff1f",
    },
    "tab.no_tab_title": {
        "en": "No Tab",
        "ja": "\u30bf\u30d6\u306a\u3057",
    },
    "tab.no_tab_msg": {
        "en": "Please add a tab first.",
        "ja": "\u5148\u306b\u30bf\u30d6\u3092\u8ffd\u52a0\u3057\u3066\u304f\u3060\u3055\u3044\u3002",
    },
    "tab.no_paths_title": {
        "en": "No Paths",
        "ja": "\u30d1\u30b9\u306a\u3057",
    },
    "tab.no_paths_msg": {
        "en": "No folders registered in this tab.",
        "ja": "\u3053\u306e\u30bf\u30d6\u306b\u30d5\u30a9\u30eb\u30c0\u304c\u767b\u9332\u3055\u308c\u3066\u3044\u307e\u305b\u3093\u3002",
    },
    "tab.open_as_tabs": {
        "en": "Open as Tabs",
        "ja": "\u30bf\u30d6\u3067\u958b\u304f",
    },

    # --- Path operations ---
    "path.move_up": {
        "en": "\u25b2 Up",
        "ja": "\u25b2 \u4e0a\u3078",
    },
    "path.move_down": {
        "en": "\u25bc Down",
        "ja": "\u25bc \u4e0b\u3078",
    },
    "path.add": {
        "en": "+ Add Path",
        "ja": "+ \u30d1\u30b9\u8ffd\u52a0",
    },
    "path.remove": {
        "en": "- Remove",
        "ja": "- \u30d1\u30b9\u524a\u9664",
    },
    "path.browse": {
        "en": "Browse...",
        "ja": "\u53c2\u7167...",
    },
    "path.invalid_title": {
        "en": "Invalid Path",
        "ja": "\u7121\u52b9\u306a\u30d1\u30b9",
    },
    "path.invalid_msg": {
        "en": "Folder does not exist:\n{path}",
        "ja": "\u30d5\u30a9\u30eb\u30c0\u304c\u5b58\u5728\u3057\u307e\u305b\u3093:\n{path}",
    },

    # --- Error messages ---
    "error.title": {
        "en": "Error",
        "ja": "\u30a8\u30e9\u30fc",
    },
    "error.open_failed": {
        "en": "Failed to open:\n{path}\n\n{error}",
        "ja": "\u958b\u3051\u307e\u305b\u3093\u3067\u3057\u305f:\n{path}\n\n{error}",
    },
    "error.invalid_paths_title": {
        "en": "Invalid Paths",
        "ja": "\u7121\u52b9\u306a\u30d1\u30b9",
    },
    "error.invalid_paths_msg": {
        "en": "The following paths will be skipped:\n{paths}",
        "ja": "\u4ee5\u4e0b\u306e\u30d1\u30b9\u306f\u30b9\u30ad\u30c3\u30d7\u3055\u308c\u307e\u3059:\n{paths}",
    },

    # --- Settings ---
    "settings.timeout": {
        "en": "Timeout",
        "ja": "\u30bf\u30a4\u30e0\u30a2\u30a6\u30c8",
    },
    "settings.timeout_unit": {
        "en": "sec",
        "ja": "\u79d2",
    },
}

# Current language
_current_lang: str = LANG_EN


def detect_system_language() -> str:
    """Detect the system language and return the best matching language code."""
    try:
        lang_code = locale.getdefaultlocale()[0] or ""
        lang_code = lang_code.lower()
        if lang_code.startswith("ja"):
            return LANG_JA
    except Exception:
        pass
    return LANG_EN


def set_language(lang: str) -> None:
    """Set the current language."""
    global _current_lang
    if lang in (LANG_EN, LANG_JA):
        _current_lang = lang
        log.info("Language set to: %s", lang)
    else:
        log.warning("Unsupported language: %s, falling back to en", lang)
        _current_lang = LANG_EN


def get_language() -> str:
    """Get the current language code."""
    return _current_lang


def t(key: str, **kwargs: str) -> str:
    """
    Get a translated string by key.

    Supports format placeholders: t("key", path="/foo") replaces {path}.
    Falls back to English if the key or language is missing.
    """
    entry = _STRINGS.get(key)
    if entry is None:
        log.warning("Missing i18n key: %s", key)
        return key

    text = entry.get(_current_lang) or entry.get(LANG_EN, key)
    if kwargs:
        try:
            text = text.format(**kwargs)
        except KeyError:
            pass
    return text


def init() -> None:
    """Initialize i18n: detect system language and set it."""
    lang = detect_system_language()
    set_language(lang)
