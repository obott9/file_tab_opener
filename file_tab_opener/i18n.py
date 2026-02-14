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
LANG_KO: Final[str] = "ko"
LANG_ZH_TW: Final[str] = "zh_TW"
LANG_ZH_CN: Final[str] = "zh_CN"

# Display names for the language switcher UI
LANG_NAMES: Final[dict[str, str]] = {
    LANG_EN: "English",
    LANG_JA: "日本語",
    LANG_KO: "한국어",
    LANG_ZH_TW: "繁體中文",
    LANG_ZH_CN: "简体中文",
}

# Ordered list of supported languages
SUPPORTED_LANGS: Final[list[str]] = [LANG_EN, LANG_JA, LANG_KO, LANG_ZH_TW, LANG_ZH_CN]

# Translation table: key -> {lang: text}
_STRINGS: Final[dict[str, dict[str, str]]] = {
    # --- App ---
    "app.title": {
        "en": "File Tab Opener",
        "ja": "File Tab Opener",
        "ko": "File Tab Opener",
        "zh_TW": "File Tab Opener",
        "zh_CN": "File Tab Opener",
    },

    # --- History section ---
    "history.label": {
        "en": "History:",
        "ja": "履歴:",
        "ko": "기록:",
        "zh_TW": "歷史:",
        "zh_CN": "历史:",
    },
    "history.open_finder": {
        "en": "Open in Finder",
        "ja": "Finderで開く",
        "ko": "Finder에서 열기",
        "zh_TW": "在 Finder 中開啟",
        "zh_CN": "在 Finder 中打开",
    },
    "history.open_explorer": {
        "en": "Open in Explorer",
        "ja": "エクスプローラーで開く",
        "ko": "탐색기에서 열기",
        "zh_TW": "在檔案總管中開啟",
        "zh_CN": "在资源管理器中打开",
    },
    "history.pin": {
        "en": "Pin",
        "ja": "Pin",
        "ko": "Pin",
        "zh_TW": "Pin",
        "zh_CN": "Pin",
    },
    "history.clear": {
        "en": "Clear",
        "ja": "Clear",
        "ko": "Clear",
        "zh_TW": "Clear",
        "zh_CN": "Clear",
    },
    "history.clear_confirm_title": {
        "en": "Clear History",
        "ja": "履歴クリア",
        "ko": "기록 지우기",
        "zh_TW": "清除歷史",
        "zh_CN": "清除历史",
    },
    "history.clear_confirm_msg": {
        "en": "Delete all history except pinned items?",
        "ja": "ピン留め以外の履歴をすべて削除しますか？",
        "ko": "고정된 항목을 제외한 모든 기록을 삭제하시겠습니까?",
        "zh_TW": "是否刪除所有未釘選的歷史記錄？",
        "zh_CN": "是否删除所有未固定的历史记录？",
    },
    "history.invalid_path_title": {
        "en": "Invalid Path",
        "ja": "無効なパス",
        "ko": "잘못된 경로",
        "zh_TW": "無效路徑",
        "zh_CN": "无效路径",
    },
    "history.invalid_path_msg": {
        "en": "Folder does not exist:\n{path}",
        "ja": "フォルダが存在しません:\n{path}",
        "ko": "폴더가 존재하지 않습니다:\n{path}",
        "zh_TW": "資料夾不存在：\n{path}",
        "zh_CN": "文件夹不存在：\n{path}",
    },

    # --- Tab group section ---
    "tab.add": {
        "en": "+ Add Tab",
        "ja": "+ タブ追加",
        "ko": "+ 탭 추가",
        "zh_TW": "+ 新增分頁",
        "zh_CN": "+ 添加标签",
    },
    "tab.delete": {
        "en": "x Delete Tab",
        "ja": "x タブ削除",
        "ko": "x 탭 삭제",
        "zh_TW": "x 刪除分頁",
        "zh_CN": "x 删除标签",
    },
    "tab.add_dialog_title": {
        "en": "Add Tab",
        "ja": "タブ追加",
        "ko": "탭 추가",
        "zh_TW": "新增分頁",
        "zh_CN": "添加标签",
    },
    "tab.add_dialog_prompt": {
        "en": "Enter tab name:",
        "ja": "タブ名を入力:",
        "ko": "탭 이름 입력:",
        "zh_TW": "輸入分頁名稱：",
        "zh_CN": "输入标签名称：",
    },
    "tab.duplicate_title": {
        "en": "Duplicate",
        "ja": "重複",
        "ko": "중복",
        "zh_TW": "重複",
        "zh_CN": "重复",
    },
    "tab.duplicate_msg": {
        "en": "Tab '{name}' already exists.",
        "ja": "タブ '{name}' は既に存在します。",
        "ko": "탭 '{name}'이(가) 이미 존재합니다.",
        "zh_TW": "分頁 '{name}' 已存在。",
        "zh_CN": "标签 '{name}' 已存在。",
    },
    "tab.move_left": {
        "en": "\u25c0",
        "ja": "\u25c0",
        "ko": "\u25c0",
        "zh_TW": "\u25c0",
        "zh_CN": "\u25c0",
    },
    "tab.move_right": {
        "en": "\u25b6",
        "ja": "\u25b6",
        "ko": "\u25b6",
        "zh_TW": "\u25b6",
        "zh_CN": "\u25b6",
    },
    "tab.rename": {
        "en": "Rename",
        "ja": "名前変更",
        "ko": "이름 변경",
        "zh_TW": "重新命名",
        "zh_CN": "重命名",
    },
    "tab.rename_dialog_title": {
        "en": "Rename Tab",
        "ja": "タブ名変更",
        "ko": "탭 이름 변경",
        "zh_TW": "重新命名分頁",
        "zh_CN": "重命名标签",
    },
    "tab.rename_dialog_prompt": {
        "en": "Enter new name:",
        "ja": "新しいタブ名を入力:",
        "ko": "새 이름 입력:",
        "zh_TW": "輸入新名稱：",
        "zh_CN": "输入新名称：",
    },
    "tab.delete_confirm_title": {
        "en": "Delete Tab",
        "ja": "タブ削除",
        "ko": "탭 삭제",
        "zh_TW": "刪除分頁",
        "zh_CN": "删除标签",
    },
    "tab.delete_confirm_msg": {
        "en": "Delete tab '{name}' and all its paths?",
        "ja": "タブ '{name}' とそのパスをすべて削除しますか？",
        "ko": "탭 '{name}'과(와) 모든 경로를 삭제하시겠습니까?",
        "zh_TW": "是否刪除分頁 '{name}' 及其所有路徑？",
        "zh_CN": "是否删除标签 '{name}' 及其所有路径？",
    },
    "tab.no_tab_title": {
        "en": "No Tab",
        "ja": "タブなし",
        "ko": "탭 없음",
        "zh_TW": "無分頁",
        "zh_CN": "无标签",
    },
    "tab.no_tab_msg": {
        "en": "Please add a tab first.",
        "ja": "先にタブを追加してください。",
        "ko": "먼저 탭을 추가하세요.",
        "zh_TW": "請先新增分頁。",
        "zh_CN": "请先添加标签。",
    },
    "tab.no_paths_title": {
        "en": "No Paths",
        "ja": "パスなし",
        "ko": "경로 없음",
        "zh_TW": "無路徑",
        "zh_CN": "无路径",
    },
    "tab.no_paths_msg": {
        "en": "No folders registered in this tab.",
        "ja": "このタブにフォルダが登録されていません。",
        "ko": "이 탭에 등록된 폴더가 없습니다.",
        "zh_TW": "此分頁未註冊任何資料夾。",
        "zh_CN": "此标签未注册任何文件夹。",
    },
    "tab.open_as_tabs": {
        "en": "Open as Tabs",
        "ja": "タブで開く",
        "ko": "탭으로 열기",
        "zh_TW": "以分頁開啟",
        "zh_CN": "以标签打开",
    },

    # --- Path operations ---
    "path.move_up": {
        "en": "\u25b2 Up",
        "ja": "\u25b2 上へ",
        "ko": "\u25b2 위로",
        "zh_TW": "\u25b2 上移",
        "zh_CN": "\u25b2 上移",
    },
    "path.move_down": {
        "en": "\u25bc Down",
        "ja": "\u25bc 下へ",
        "ko": "\u25bc 아래로",
        "zh_TW": "\u25bc 下移",
        "zh_CN": "\u25bc 下移",
    },
    "path.add": {
        "en": "+ Add Path",
        "ja": "+ パス追加",
        "ko": "+ 경로 추가",
        "zh_TW": "+ 新增路徑",
        "zh_CN": "+ 添加路径",
    },
    "path.remove": {
        "en": "- Remove",
        "ja": "- パス削除",
        "ko": "- 경로 삭제",
        "zh_TW": "- 移除路徑",
        "zh_CN": "- 删除路径",
    },
    "path.browse": {
        "en": "Browse...",
        "ja": "参照...",
        "ko": "찾아보기...",
        "zh_TW": "瀏覽...",
        "zh_CN": "浏览...",
    },
    "path.placeholder": {
        "en": "Enter folder path...",
        "ja": "フォルダパスを入力...",
        "ko": "폴더 경로 입력...",
        "zh_TW": "輸入資料夾路徑...",
        "zh_CN": "输入文件夹路径...",
    },
    "path.invalid_title": {
        "en": "Invalid Path",
        "ja": "無効なパス",
        "ko": "잘못된 경로",
        "zh_TW": "無效路徑",
        "zh_CN": "无效路径",
    },
    "path.invalid_msg": {
        "en": "Folder does not exist:\n{path}",
        "ja": "フォルダが存在しません:\n{path}",
        "ko": "폴더가 존재하지 않습니다:\n{path}",
        "zh_TW": "資料夾不存在：\n{path}",
        "zh_CN": "文件夹不存在：\n{path}",
    },

    # --- Error messages ---
    "error.title": {
        "en": "Error",
        "ja": "エラー",
        "ko": "오류",
        "zh_TW": "錯誤",
        "zh_CN": "错误",
    },
    "error.open_failed": {
        "en": "Failed to open:\n{path}\n\n{error}",
        "ja": "開けませんでした:\n{path}\n\n{error}",
        "ko": "열 수 없습니다:\n{path}\n\n{error}",
        "zh_TW": "無法開啟：\n{path}\n\n{error}",
        "zh_CN": "无法打开：\n{path}\n\n{error}",
    },
    "error.invalid_paths_title": {
        "en": "Invalid Paths",
        "ja": "無効なパス",
        "ko": "잘못된 경로",
        "zh_TW": "無效路徑",
        "zh_CN": "无效路径",
    },
    "error.invalid_paths_msg": {
        "en": "The following paths will be skipped:\n{paths}",
        "ja": "以下のパスはスキップされます:\n{paths}",
        "ko": "다음 경로는 건너뜁니다:\n{paths}",
        "zh_TW": "以下路徑將被跳過：\n{paths}",
        "zh_CN": "以下路径将被跳过：\n{paths}",
    },

    # --- Window geometry ---
    "window.x": {
        "en": "X:",
        "ja": "X:",
        "ko": "X:",
        "zh_TW": "X:",
        "zh_CN": "X:",
    },
    "window.y": {
        "en": "Y:",
        "ja": "Y:",
        "ko": "Y:",
        "zh_TW": "Y:",
        "zh_CN": "Y:",
    },
    "window.width": {
        "en": "Width:",
        "ja": "幅:",
        "ko": "너비:",
        "zh_TW": "寬度:",
        "zh_CN": "宽度:",
    },
    "window.height": {
        "en": "Height:",
        "ja": "高さ:",
        "ko": "높이:",
        "zh_TW": "高度:",
        "zh_CN": "高度:",
    },

    "window.get_from_finder": {
        "en": "Get from Finder",
        "ja": "Finderから取得",
        "ko": "Finder에서 가져오기",
        "zh_TW": "從 Finder 取得",
        "zh_CN": "从 Finder 获取",
    },
    "window.no_finder_title": {
        "en": "No Finder Window",
        "ja": "Finderウィンドウなし",
        "ko": "Finder 창 없음",
        "zh_TW": "無 Finder 視窗",
        "zh_CN": "无 Finder 窗口",
    },
    "window.no_finder_msg": {
        "en": "No Finder window is open.",
        "ja": "Finderウィンドウが開いていません。",
        "ko": "열려 있는 Finder 창이 없습니다.",
        "zh_TW": "沒有開啟的 Finder 視窗。",
        "zh_CN": "没有打开的 Finder 窗口。",
    },

    # --- Settings ---
    "settings.timeout": {
        "en": "Timeout",
        "ja": "タイムアウト",
        "ko": "시간 제한",
        "zh_TW": "逾時",
        "zh_CN": "超时",
    },
    "settings.timeout_unit": {
        "en": "sec",
        "ja": "秒",
        "ko": "초",
        "zh_TW": "秒",
        "zh_CN": "秒",
    },
}

# Current language
_current_lang: str = LANG_EN


def detect_system_language() -> str:
    """Detect the system language and return the best matching language code."""
    try:
        lang_code = locale.getlocale()[0] or ""
        lang_code = lang_code.lower()
        if lang_code.startswith("ja"):
            return LANG_JA
        if lang_code.startswith("ko"):
            return LANG_KO
        if lang_code.startswith("zh"):
            # zh_TW, zh_HK, zh_Hant -> Traditional; otherwise -> Simplified
            if any(tag in lang_code for tag in ("tw", "hk", "hant")):
                return LANG_ZH_TW
            return LANG_ZH_CN
    except Exception:
        pass
    return LANG_EN


def set_language(lang: str) -> None:
    """Set the current language."""
    global _current_lang
    if lang in SUPPORTED_LANGS:
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
