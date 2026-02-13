"""Tests for i18n module.

Covers: language detection, translation lookup, placeholder formatting,
fallback behavior, and key completeness.
"""

from __future__ import annotations

from unittest import mock

import pytest

from file_tab_opener import i18n
from file_tab_opener.i18n import LANG_EN, LANG_JA, _STRINGS


# ============================================================
# Fixtures
# ============================================================


@pytest.fixture(autouse=True)
def reset_language() -> None:
    """Reset language to English before each test."""
    i18n.set_language(LANG_EN)


# ============================================================
# Language detection
# ============================================================


class TestLanguageDetection:
    """Test system language detection."""

    def test_detect_japanese(self) -> None:
        """Japanese locale should detect as 'ja'."""
        with mock.patch("locale.getdefaultlocale", return_value=("ja_JP", "UTF-8")):
            assert i18n.detect_system_language() == LANG_JA

    def test_detect_english(self) -> None:
        """English locale should detect as 'en'."""
        with mock.patch("locale.getdefaultlocale", return_value=("en_US", "UTF-8")):
            assert i18n.detect_system_language() == LANG_EN

    def test_detect_unknown_falls_back_to_en(self) -> None:
        """Unknown locale should fall back to English."""
        with mock.patch("locale.getdefaultlocale", return_value=("ko_KR", "UTF-8")):
            assert i18n.detect_system_language() == LANG_EN

    def test_detect_none_locale(self) -> None:
        """None locale should fall back to English."""
        with mock.patch("locale.getdefaultlocale", return_value=(None, None)):
            assert i18n.detect_system_language() == LANG_EN

    def test_detect_exception(self) -> None:
        """Exception in locale detection should fall back to English."""
        with mock.patch("locale.getdefaultlocale", side_effect=ValueError):
            assert i18n.detect_system_language() == LANG_EN


# ============================================================
# set/get language
# ============================================================


class TestSetGetLanguage:
    """Test language setting and getting."""

    def test_set_valid_language(self) -> None:
        """Setting a valid language should update the current language."""
        i18n.set_language(LANG_JA)
        assert i18n.get_language() == LANG_JA

    def test_set_invalid_language_falls_back(self) -> None:
        """Setting an invalid language should fall back to English."""
        i18n.set_language("xx")
        assert i18n.get_language() == LANG_EN

    def test_init_sets_language(self) -> None:
        """init() should detect and set the system language."""
        with mock.patch("locale.getdefaultlocale", return_value=("ja_JP", "UTF-8")):
            i18n.init()
            assert i18n.get_language() == LANG_JA


# ============================================================
# Translation lookup
# ============================================================


class TestTranslation:
    """Test the t() translation function."""

    def test_english_translation(self) -> None:
        """t() should return English text when language is English."""
        i18n.set_language(LANG_EN)
        assert i18n.t("app.title") == "File Tab Opener"

    def test_japanese_translation(self) -> None:
        """t() should return Japanese text when language is Japanese."""
        i18n.set_language(LANG_JA)
        result = i18n.t("history.label")
        assert result == "履歴:"

    def test_missing_key_returns_key(self) -> None:
        """Missing key should return the key itself."""
        result = i18n.t("nonexistent.key")
        assert result == "nonexistent.key"

    def test_placeholder_formatting(self) -> None:
        """Placeholders should be replaced with provided values."""
        i18n.set_language(LANG_EN)
        result = i18n.t("history.invalid_path_msg", path="/test/path")
        assert "/test/path" in result

    def test_placeholder_missing_kwarg(self) -> None:
        """Missing kwargs should not raise (graceful handling)."""
        i18n.set_language(LANG_EN)
        # This key has {path} placeholder, but we don't provide it
        result = i18n.t("history.invalid_path_msg")
        # Should return the raw template without error
        assert "{path}" in result

    def test_japanese_placeholder(self) -> None:
        """Japanese text with placeholders should work correctly."""
        i18n.set_language(LANG_JA)
        result = i18n.t("tab.duplicate_msg", name="テスト")
        assert "テスト" in result


# ============================================================
# Key completeness
# ============================================================


class TestKeyCompleteness:
    """Verify that all i18n keys have translations for all supported languages."""

    def test_all_keys_have_english(self) -> None:
        """Every key must have an English translation."""
        for key, translations in _STRINGS.items():
            assert LANG_EN in translations, f"Key '{key}' missing English translation"

    def test_all_keys_have_japanese(self) -> None:
        """Every key must have a Japanese translation."""
        for key, translations in _STRINGS.items():
            assert LANG_JA in translations, f"Key '{key}' missing Japanese translation"

    def test_no_empty_translations(self) -> None:
        """No translation value should be empty."""
        for key, translations in _STRINGS.items():
            for lang, text in translations.items():
                assert text != "", f"Key '{key}' has empty {lang} translation"

    def test_placeholders_consistent(self) -> None:
        """All languages should have the same placeholders for each key."""
        import re

        placeholder_re = re.compile(r"\{(\w+)\}")
        for key, translations in _STRINGS.items():
            placeholders_by_lang: dict[str, set[str]] = {}
            for lang, text in translations.items():
                placeholders_by_lang[lang] = set(placeholder_re.findall(text))

            langs = list(placeholders_by_lang.keys())
            if len(langs) < 2:
                continue
            first = placeholders_by_lang[langs[0]]
            for lang in langs[1:]:
                assert placeholders_by_lang[lang] == first, (
                    f"Key '{key}': placeholder mismatch between "
                    f"{langs[0]}={first} and {lang}={placeholders_by_lang[lang]}"
                )
