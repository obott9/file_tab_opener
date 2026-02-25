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
        LANG_EN: "File Tab Opener",
        LANG_JA: "File Tab Opener",
        LANG_KO: "File Tab Opener",
        LANG_ZH_TW: "File Tab Opener",
        LANG_ZH_CN: "File Tab Opener",
    },

    # --- History section ---
    "history.label": {
        LANG_EN: "History:",
        LANG_JA: "履歴:",
        LANG_KO: "기록:",
        LANG_ZH_TW: "歷史:",
        LANG_ZH_CN: "历史:",
    },
    "history.open_finder": {
        LANG_EN: "Open in Finder",
        LANG_JA: "Finderで開く",
        LANG_KO: "Finder에서 열기",
        LANG_ZH_TW: "在 Finder 中開啟",
        LANG_ZH_CN: "在 Finder 中打开",
    },
    "history.open_explorer": {
        LANG_EN: "Open in Explorer",
        LANG_JA: "エクスプローラーで開く",
        LANG_KO: "탐색기에서 열기",
        LANG_ZH_TW: "在檔案總管中開啟",
        LANG_ZH_CN: "在资源管理器中打开",
    },
    "history.pin": {
        LANG_EN: "Pin",
        LANG_JA: "Pin",
        LANG_KO: "Pin",
        LANG_ZH_TW: "Pin",
        LANG_ZH_CN: "Pin",
    },
    "history.clear": {
        LANG_EN: "Clear",
        LANG_JA: "Clear",
        LANG_KO: "Clear",
        LANG_ZH_TW: "Clear",
        LANG_ZH_CN: "Clear",
    },
    "history.clear_confirm_title": {
        LANG_EN: "Clear History",
        LANG_JA: "履歴クリア",
        LANG_KO: "기록 지우기",
        LANG_ZH_TW: "清除歷史",
        LANG_ZH_CN: "清除历史",
    },
    "history.clear_confirm_msg": {
        LANG_EN: "Delete all history except pinned items?",
        LANG_JA: "ピン留め以外の履歴をすべて削除しますか？",
        LANG_KO: "고정된 항목을 제외한 모든 기록을 삭제하시겠습니까?",
        LANG_ZH_TW: "是否刪除所有未釘選的歷史記錄？",
        LANG_ZH_CN: "是否删除所有未固定的历史记录？",
    },
    "history.invalid_path_title": {
        LANG_EN: "Invalid Path",
        LANG_JA: "無効なパス",
        LANG_KO: "잘못된 경로",
        LANG_ZH_TW: "無效路徑",
        LANG_ZH_CN: "无效路径",
    },
    "history.invalid_path_msg": {
        LANG_EN: "Folder does not exist:\n{path}",
        LANG_JA: "フォルダが存在しません:\n{path}",
        LANG_KO: "폴더가 존재하지 않습니다:\n{path}",
        LANG_ZH_TW: "資料夾不存在：\n{path}",
        LANG_ZH_CN: "文件夹不存在：\n{path}",
    },

    # --- Tab group section ---
    "tab.add": {
        LANG_EN: "+ Add Tab",
        LANG_JA: "+ タブ追加",
        LANG_KO: "+ 탭 추가",
        LANG_ZH_TW: "+ 新增分頁",
        LANG_ZH_CN: "+ 添加标签",
    },
    "tab.delete": {
        LANG_EN: "x Delete Tab",
        LANG_JA: "x タブ削除",
        LANG_KO: "x 탭 삭제",
        LANG_ZH_TW: "x 刪除分頁",
        LANG_ZH_CN: "x 删除标签",
    },
    "tab.add_dialog_title": {
        LANG_EN: "Add Tab",
        LANG_JA: "タブ追加",
        LANG_KO: "탭 추가",
        LANG_ZH_TW: "新增分頁",
        LANG_ZH_CN: "添加标签",
    },
    "tab.add_dialog_prompt": {
        LANG_EN: "Enter tab name:",
        LANG_JA: "タブ名を入力:",
        LANG_KO: "탭 이름 입력:",
        LANG_ZH_TW: "輸入分頁名稱：",
        LANG_ZH_CN: "输入标签名称：",
    },
    "tab.duplicate_title": {
        LANG_EN: "Duplicate",
        LANG_JA: "重複",
        LANG_KO: "중복",
        LANG_ZH_TW: "重複",
        LANG_ZH_CN: "重复",
    },
    "tab.duplicate_msg": {
        LANG_EN: "Tab '{name}' already exists.",
        LANG_JA: "タブ '{name}' は既に存在します。",
        LANG_KO: "탭 '{name}'이(가) 이미 존재합니다.",
        LANG_ZH_TW: "分頁 '{name}' 已存在。",
        LANG_ZH_CN: "标签 '{name}' 已存在。",
    },
    "tab.copy": {
        LANG_EN: "Copy Tab",
        LANG_JA: "タブ複製",
        LANG_KO: "탭 복사",
        LANG_ZH_TW: "複製分頁",
        LANG_ZH_CN: "复制标签",
    },
    "tab.move_left": {
        LANG_EN: "\u25c0",
        LANG_JA: "\u25c0",
        LANG_KO: "\u25c0",
        LANG_ZH_TW: "\u25c0",
        LANG_ZH_CN: "\u25c0",
    },
    "tab.move_right": {
        LANG_EN: "\u25b6",
        LANG_JA: "\u25b6",
        LANG_KO: "\u25b6",
        LANG_ZH_TW: "\u25b6",
        LANG_ZH_CN: "\u25b6",
    },
    "tab.rename": {
        LANG_EN: "Rename",
        LANG_JA: "名前変更",
        LANG_KO: "이름 변경",
        LANG_ZH_TW: "重新命名",
        LANG_ZH_CN: "重命名",
    },
    "tab.rename_dialog_title": {
        LANG_EN: "Rename Tab",
        LANG_JA: "タブ名変更",
        LANG_KO: "탭 이름 변경",
        LANG_ZH_TW: "重新命名分頁",
        LANG_ZH_CN: "重命名标签",
    },
    "tab.rename_dialog_prompt": {
        LANG_EN: "Enter new name:",
        LANG_JA: "新しいタブ名を入力:",
        LANG_KO: "새 이름 입력:",
        LANG_ZH_TW: "輸入新名稱：",
        LANG_ZH_CN: "输入新名称：",
    },
    "tab.delete_confirm_title": {
        LANG_EN: "Delete Tab",
        LANG_JA: "タブ削除",
        LANG_KO: "탭 삭제",
        LANG_ZH_TW: "刪除分頁",
        LANG_ZH_CN: "删除标签",
    },
    "tab.delete_confirm_msg": {
        LANG_EN: "Delete tab '{name}' and all its paths?",
        LANG_JA: "タブ '{name}' とそのパスをすべて削除しますか？",
        LANG_KO: "탭 '{name}'과(와) 모든 경로를 삭제하시겠습니까?",
        LANG_ZH_TW: "是否刪除分頁 '{name}' 及其所有路徑？",
        LANG_ZH_CN: "是否删除标签 '{name}' 及其所有路径？",
    },
    "tab.no_tab_title": {
        LANG_EN: "No Tab",
        LANG_JA: "タブなし",
        LANG_KO: "탭 없음",
        LANG_ZH_TW: "無分頁",
        LANG_ZH_CN: "无标签",
    },
    "tab.no_tab_msg": {
        LANG_EN: "Please add a tab first.",
        LANG_JA: "先にタブを追加してください。",
        LANG_KO: "먼저 탭을 추가하세요.",
        LANG_ZH_TW: "請先新增分頁。",
        LANG_ZH_CN: "请先添加标签。",
    },
    "tab.no_paths_title": {
        LANG_EN: "No Paths",
        LANG_JA: "パスなし",
        LANG_KO: "경로 없음",
        LANG_ZH_TW: "無路徑",
        LANG_ZH_CN: "无路径",
    },
    "tab.no_paths_msg": {
        LANG_EN: "No folders registered in this tab.",
        LANG_JA: "このタブにフォルダが登録されていません。",
        LANG_KO: "이 탭에 등록된 폴더가 없습니다.",
        LANG_ZH_TW: "此分頁未註冊任何資料夾。",
        LANG_ZH_CN: "此标签未注册任何文件夹。",
    },
    "tab.open_as_tabs": {
        LANG_EN: "Open as Tabs",
        LANG_JA: "タブで開く",
        LANG_KO: "탭으로 열기",
        LANG_ZH_TW: "以分頁開啟",
        LANG_ZH_CN: "以标签打开",
    },

    # --- Path operations ---
    "path.move_up": {
        LANG_EN: "\u25b2 Up",
        LANG_JA: "\u25b2 上へ",
        LANG_KO: "\u25b2 위로",
        LANG_ZH_TW: "\u25b2 上移",
        LANG_ZH_CN: "\u25b2 上移",
    },
    "path.move_down": {
        LANG_EN: "\u25bc Down",
        LANG_JA: "\u25bc 下へ",
        LANG_KO: "\u25bc 아래로",
        LANG_ZH_TW: "\u25bc 下移",
        LANG_ZH_CN: "\u25bc 下移",
    },
    "path.add": {
        LANG_EN: "+ Add Path",
        LANG_JA: "+ パス追加",
        LANG_KO: "+ 경로 추가",
        LANG_ZH_TW: "+ 新增路徑",
        LANG_ZH_CN: "+ 添加路径",
    },
    "path.remove": {
        LANG_EN: "- Remove",
        LANG_JA: "- パス削除",
        LANG_KO: "- 경로 삭제",
        LANG_ZH_TW: "- 移除路徑",
        LANG_ZH_CN: "- 删除路径",
    },
    "path.browse": {
        LANG_EN: "Browse...",
        LANG_JA: "参照...",
        LANG_KO: "찾아보기...",
        LANG_ZH_TW: "瀏覽...",
        LANG_ZH_CN: "浏览...",
    },
    "path.placeholder": {
        LANG_EN: "Enter folder path...",
        LANG_JA: "フォルダパスを入力...",
        LANG_KO: "폴더 경로 입력...",
        LANG_ZH_TW: "輸入資料夾路徑...",
        LANG_ZH_CN: "输入文件夹路径...",
    },
    "path.invalid_title": {
        LANG_EN: "Invalid Path",
        LANG_JA: "無効なパス",
        LANG_KO: "잘못된 경로",
        LANG_ZH_TW: "無效路徑",
        LANG_ZH_CN: "无效路径",
    },
    "path.invalid_msg": {
        LANG_EN: "Folder does not exist:\n{path}",
        LANG_JA: "フォルダが存在しません:\n{path}",
        LANG_KO: "폴더가 존재하지 않습니다:\n{path}",
        LANG_ZH_TW: "資料夾不存在：\n{path}",
        LANG_ZH_CN: "文件夹不存在：\n{path}",
    },

    # --- Error messages ---
    "error.title": {
        LANG_EN: "Error",
        LANG_JA: "エラー",
        LANG_KO: "오류",
        LANG_ZH_TW: "錯誤",
        LANG_ZH_CN: "错误",
    },
    "error.open_failed": {
        LANG_EN: "Failed to open:\n{path}\n\n{error}",
        LANG_JA: "開けませんでした:\n{path}\n\n{error}",
        LANG_KO: "열 수 없습니다:\n{path}\n\n{error}",
        LANG_ZH_TW: "無法開啟：\n{path}\n\n{error}",
        LANG_ZH_CN: "无法打开：\n{path}\n\n{error}",
    },
    "error.invalid_paths_title": {
        LANG_EN: "Invalid Paths",
        LANG_JA: "無効なパス",
        LANG_KO: "잘못된 경로",
        LANG_ZH_TW: "無效路徑",
        LANG_ZH_CN: "无效路径",
    },
    "error.invalid_paths_msg": {
        LANG_EN: "The following paths will be skipped:\n{paths}",
        LANG_JA: "以下のパスはスキップされます:\n{paths}",
        LANG_KO: "다음 경로는 건너뜁니다:\n{paths}",
        LANG_ZH_TW: "以下路徑將被跳過：\n{paths}",
        LANG_ZH_CN: "以下路径将被跳过：\n{paths}",
    },
    "error.accessibility_required": {
        LANG_EN: "Accessibility permission required.\n"
              "Go to System Settings → Privacy & Security → Accessibility\n"
              "and enable access for Terminal.app.",
        LANG_JA: "アクセシビリティの許可が必要です。\n"
              "システム設定 → プライバシーとセキュリティ → アクセシビリティ\n"
              "でTerminal.appのアクセスを有効にしてください。",
        LANG_KO: "손쉬운 사용 권한이 필요합니다.\n"
              "시스템 설정 → 개인정보 보호 및 보안 → 손쉬운 사용\n"
              "에서 Terminal.app의 접근을 허용하세요.",
        LANG_ZH_TW: "需要輔助使用權限。\n"
                 "前往系統設定 → 隱私與安全性 → 輔助使用\n"
                 "並啟用 Terminal.app 的存取權限。",
        LANG_ZH_CN: "需要辅助功能权限。\n"
                 "前往系统设置 → 隐私与安全性 → 辅助功能\n"
                 "并启用 Terminal.app 的访问权限。",
    },

    # --- Toast notification ---
    "toast.progress_header": {
        LANG_EN: "Opening tabs... ({current}/{total})",
        LANG_JA: "タブを展開中... ({current}/{total})",
        LANG_KO: "탭 열는 중... ({current}/{total})",
        LANG_ZH_TW: "正在開啟分頁... ({current}/{total})",
        LANG_ZH_CN: "正在打开标签页... ({current}/{total})",
    },
    "toast.wait_message": {
        LANG_EN: "Please wait.\nDo not use the keyboard or mouse.",
        LANG_JA: "しばらくお待ちください。\nキーボード・マウスを操作しないでください",
        LANG_KO: "잠시 기다려 주세요.\n키보드와 마우스를 사용하지 마세요.",
        LANG_ZH_TW: "請稍候。\n請勿使用鍵盤或滑鼠。",
        LANG_ZH_CN: "请稍候。\n请勿使用键盘或鼠标。",
    },

    # --- Window geometry ---
    "window.x": {
        LANG_EN: "X:",
        LANG_JA: "X:",
        LANG_KO: "X:",
        LANG_ZH_TW: "X:",
        LANG_ZH_CN: "X:",
    },
    "window.y": {
        LANG_EN: "Y:",
        LANG_JA: "Y:",
        LANG_KO: "Y:",
        LANG_ZH_TW: "Y:",
        LANG_ZH_CN: "Y:",
    },
    "window.width": {
        LANG_EN: "Width:",
        LANG_JA: "幅:",
        LANG_KO: "너비:",
        LANG_ZH_TW: "寬度:",
        LANG_ZH_CN: "宽度:",
    },
    "window.height": {
        LANG_EN: "Height:",
        LANG_JA: "高さ:",
        LANG_KO: "높이:",
        LANG_ZH_TW: "高度:",
        LANG_ZH_CN: "高度:",
    },

    "window.get_from_finder": {
        LANG_EN: "Get from Finder",
        LANG_JA: "Finderから取得",
        LANG_KO: "Finder에서 가져오기",
        LANG_ZH_TW: "從 Finder 取得",
        LANG_ZH_CN: "从 Finder 获取",
    },
    "window.no_finder_title": {
        LANG_EN: "No Finder Window",
        LANG_JA: "Finderウィンドウなし",
        LANG_KO: "Finder 창 없음",
        LANG_ZH_TW: "無 Finder 視窗",
        LANG_ZH_CN: "无 Finder 窗口",
    },
    "window.no_finder_msg": {
        LANG_EN: "No Finder window is open.",
        LANG_JA: "Finderウィンドウが開いていません。",
        LANG_KO: "열려 있는 Finder 창이 없습니다.",
        LANG_ZH_TW: "沒有開啟的 Finder 視窗。",
        LANG_ZH_CN: "没有打开的 Finder 窗口。",
    },

    "window.get_from_explorer": {
        LANG_EN: "Get from Explorer",
        LANG_JA: "Explorerから取得",
        LANG_KO: "탐색기에서 가져오기",
        LANG_ZH_TW: "從檔案總管取得",
        LANG_ZH_CN: "从资源管理器获取",
    },
    "window.no_explorer_title": {
        LANG_EN: "No Explorer Window",
        LANG_JA: "Explorerウィンドウなし",
        LANG_KO: "탐색기 창 없음",
        LANG_ZH_TW: "無檔案總管視窗",
        LANG_ZH_CN: "无资源管理器窗口",
    },
    "window.no_explorer_msg": {
        LANG_EN: "No Explorer window is open.",
        LANG_JA: "Explorerウィンドウが開いていません。",
        LANG_KO: "열려 있는 탐색기 창이 없습니다.",
        LANG_ZH_TW: "沒有開啟的檔案總管視窗。",
        LANG_ZH_CN: "没有打开的资源管理器窗口。",
    },

    # --- Settings ---
    "settings.timeout": {
        LANG_EN: "Timeout",
        LANG_JA: "タイムアウト",
        LANG_KO: "시간 제한",
        LANG_ZH_TW: "逾時",
        LANG_ZH_CN: "超时",
    },
    "settings.timeout_unit": {
        LANG_EN: "sec",
        LANG_JA: "秒",
        LANG_KO: "초",
        LANG_ZH_TW: "秒",
        LANG_ZH_CN: "秒",
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
