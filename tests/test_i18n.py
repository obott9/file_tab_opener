"""Tests for i18n module.

Covers: language detection, translation lookup, placeholder formatting,
fallback behavior, and key completeness.
"""

from __future__ import annotations

from unittest import mock

import pytest

from file_tab_opener import i18n
from file_tab_opener.i18n import (
    LANG_EN, LANG_JA, LANG_KO, LANG_ZH_TW, LANG_ZH_CN,
    SUPPORTED_LANGS, _STRINGS,
)


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
        with mock.patch("locale.getlocale", return_value=("ja_JP", "UTF-8")):
            assert i18n.detect_system_language() == LANG_JA

    def test_detect_english(self) -> None:
        """English locale should detect as 'en'."""
        with mock.patch("locale.getlocale", return_value=("en_US", "UTF-8")):
            assert i18n.detect_system_language() == LANG_EN

    def test_detect_korean(self) -> None:
        """Korean locale should detect as 'ko'."""
        with mock.patch("locale.getlocale", return_value=("ko_KR", "UTF-8")):
            assert i18n.detect_system_language() == LANG_KO

    def test_detect_zh_tw(self) -> None:
        """Traditional Chinese (Taiwan) locale should detect as 'zh_TW'."""
        with mock.patch("locale.getlocale", return_value=("zh_TW", "UTF-8")):
            assert i18n.detect_system_language() == LANG_ZH_TW

    def test_detect_zh_hk(self) -> None:
        """Traditional Chinese (Hong Kong) locale should detect as 'zh_TW'."""
        with mock.patch("locale.getlocale", return_value=("zh_HK", "UTF-8")):
            assert i18n.detect_system_language() == LANG_ZH_TW

    def test_detect_zh_cn(self) -> None:
        """Simplified Chinese locale should detect as 'zh_CN'."""
        with mock.patch("locale.getlocale", return_value=("zh_CN", "UTF-8")):
            assert i18n.detect_system_language() == LANG_ZH_CN

    def test_detect_zh_generic(self) -> None:
        """Generic Chinese locale should default to Simplified."""
        with mock.patch("locale.getlocale", return_value=("zh", "UTF-8")):
            assert i18n.detect_system_language() == LANG_ZH_CN

    def test_detect_unknown_falls_back_to_en(self) -> None:
        """Unknown locale should fall back to English."""
        with mock.patch("locale.getlocale", return_value=("de_DE", "UTF-8")):
            assert i18n.detect_system_language() == LANG_EN

    def test_detect_none_locale(self) -> None:
        """None locale should fall back to English."""
        with mock.patch("locale.getlocale", return_value=(None, None)):
            assert i18n.detect_system_language() == LANG_EN

    def test_detect_exception(self) -> None:
        """Exception in locale detection should fall back to English."""
        with mock.patch("locale.getlocale", side_effect=ValueError):
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

    def test_set_all_supported_languages(self) -> None:
        """All supported languages should be settable."""
        for lang in SUPPORTED_LANGS:
            i18n.set_language(lang)
            assert i18n.get_language() == lang

    def test_set_invalid_language_falls_back(self) -> None:
        """Setting an invalid language should fall back to English."""
        i18n.set_language("xx")
        assert i18n.get_language() == LANG_EN

    def test_init_sets_language(self) -> None:
        """init() should detect and set the system language."""
        with mock.patch("locale.getlocale", return_value=("ja_JP", "UTF-8")):
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

    def test_korean_translation(self) -> None:
        """t() should return Korean text when language is Korean."""
        i18n.set_language(LANG_KO)
        result = i18n.t("history.label")
        assert result == "기록:"

    def test_zh_tw_translation(self) -> None:
        """t() should return Traditional Chinese text."""
        i18n.set_language(LANG_ZH_TW)
        result = i18n.t("history.label")
        assert result == "歷史:"

    def test_zh_cn_translation(self) -> None:
        """t() should return Simplified Chinese text."""
        i18n.set_language(LANG_ZH_CN)
        result = i18n.t("history.label")
        assert result == "历史:"

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

    def test_korean_placeholder(self) -> None:
        """Korean text with placeholders should work correctly."""
        i18n.set_language(LANG_KO)
        result = i18n.t("tab.duplicate_msg", name="테스트")
        assert "테스트" in result

    def test_zh_tw_placeholder(self) -> None:
        """Traditional Chinese text with placeholders should work correctly."""
        i18n.set_language(LANG_ZH_TW)
        result = i18n.t("tab.duplicate_msg", name="測試")
        assert "測試" in result


# ============================================================
# Key completeness
# ============================================================


class TestKeyCompleteness:
    """Verify that all i18n keys have translations for all supported languages."""

    def test_all_keys_have_all_languages(self) -> None:
        """Every key must have a translation for every supported language."""
        for key, translations in _STRINGS.items():
            for lang in SUPPORTED_LANGS:
                assert lang in translations, (
                    f"Key '{key}' missing {lang} translation"
                )

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
