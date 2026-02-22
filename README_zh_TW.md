# File Tab Opener

[English](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | **繁體中文** | [简体中文](README_zh_CN.md)

一個 GUI 工具，用於在 **Windows 檔案總管** 或 **macOS Finder** 的單一視窗中以分頁方式一次開啟多個資料夾。

無需逐一開啟資料夾，只要將它們註冊到命名的分頁群組中，一鍵即可全部開啟——每個資料夾會顯示為同一視窗中的獨立分頁。

## 功能

- **分頁群組管理** — 建立命名群組（例如「工作」、「個人」），並指定資料夾路徑
- **分頁群組複製** — 複製現有的分頁群組。複製名稱遵循 `"{基礎名稱} {編號}"` 格式（半形空格 + 序號）：「工作」→「工作 1」→「工作 2」。複製帶編號的分頁會擷取基礎名稱（「工作 3」→ 基礎「工作」），並指派下一個可用編號。連字號等分隔符號視為名稱的一部分（「工作-3」→「工作-3 1」）。
- **一鍵開啟** — 將群組中的所有資料夾以分頁方式在檔案總管/Finder 的單一視窗中開啟
- **歷史記錄 & 釘選** — 自動記錄最近開啟的資料夾，常用項目可釘選
- **跨平台** — 支援 Windows（檔案總管分頁，Win 11 以上）及 macOS（Finder 分頁）
- **雙主題** — 使用 [customtkinter](https://github.com/TomSchimansky/CustomTkinter) 實現現代化 UI；未安裝時回退至標準 tkinter
- **多語言** — 英文、日文、韓文、繁體中文、簡體中文（從系統地區設定自動偵測）

## 系統需求

- Python 3.10 以上
- Windows 11 以上或 macOS 12 以上

## 安裝

```bash
git clone https://github.com/obott9/file_tab_opener.git
cd file_tab_opener
pip install .
```

包含所有可選依賴項的完整安裝（建議）：

```bash
pip install .[all]
```

### 可選依賴項

| 套件 | 用途 | 安裝 |
|------|------|------|
| customtkinter | 現代主題 GUI | `pip install .[ui]` |
| pywinauto | 檔案總管分頁自動化（Windows） | `pip install .[windows]` |

## 使用方式

```bash
file-tab-opener
```

以 Python 模組執行：

```bash
python -m file_tab_opener
```

### 快速開始

1. 啟動應用程式
2. 點擊 **+ 新增分頁** 建立分頁群組（例如「專案 A」）
3. 透過文字輸入欄、**瀏覽** 按鈕或從檔案總管貼上路徑來新增資料夾路徑
4. 點擊 **以分頁開啟** 將所有資料夾以分頁方式在單一視窗中開啟

### 歷史記錄區

- 在下拉方塊中輸入/貼上資料夾路徑，點擊 **開啟**
- 路徑會自動儲存至歷史記錄
- 點擊 **Pin** 將項目固定在清單頂部
- 點擊 **Clear** 刪除所有未釘選的歷史記錄

## 運作方式

### Windows（檔案總管分頁）

三層回退機制以最大化相容性：

1. **pywinauto UIA** — 開啟新的檔案總管視窗，透過 UI Automation 連線。使用 UIA InvokePattern（「+」按鈕）建立新分頁，並透過 UIA ValuePattern 直接設定網址列路徑。Enter 使用 PostMessage（視窗指定，非全域）傳送。僅在 UIA 操作失敗時才回退至鍵盤快捷鍵。輸入後驗證路徑，失敗時自動重試。最可靠的方式。
2. **ctypes SendInput** — 使用 Win32 `SendInput` API 的相同按鍵方式。無外部依賴，但因焦點和時序問題可靠性稍低。
3. **個別視窗** — 透過 `subprocess` 在個別檔案總管視窗中開啟各資料夾的回退方案。

### macOS（Finder 分頁）

兩層回退機制：

1. **AppleScript + System Events** — 在 Finder 中開啟第一個資料夾，然後透過 ⌘T 按鍵建立新分頁，以 AppleScript 設定各分頁的目標。
2. **個別視窗** — 使用 `open` 指令在個別視窗中開啟的回退方案。

> **注意：** AppleScript 方式需要輔助使用權限。請前往 **系統設定 → 隱私與安全性 → 輔助使用**，並啟用 Terminal.app（或您使用的終端機）的存取權限。

### 效能說明（Windows）

Windows 檔案總管沒有分頁操作的公開 API。所有方式都依賴 UI 自動化或按鍵模擬（`Ctrl+T` → 網址列輸入），每個分頁都需要等待 UI 回應的 `delay`。我們已透過 UIA ValuePattern 直接輸入網址列、最小化等待時間、省略不必要的步驟等方式盡可能優化，但由於不存在原生分頁 API，這是目前的根本限制。分頁數量多時，相比 macOS（Finder 支援透過 AppleScript 直接操作分頁）會明顯較慢。

> **⚠️ 注意（ctypes SendInput 回退）：** 分頁開啟過程中請勿操作鍵盤或滑鼠。ctypes 回退方式使用 OS 層級的按鍵模擬（`SendInput`），操作期間的任何輸入可能干擾自動化流程。pywinauto UIA 方式主要使用目標指定的 UI Automation 和 PostMessage（無全域按鍵），但在 UIA 操作失敗時可能回退至鍵盤快捷鍵。

## 設定檔

設定儲存於 JSON 檔案：

| OS | 路徑 |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\config.json` |
| macOS | `~/Library/Application Support/FileTabOpener/config.json` |
| Linux | `~/.config/file_tab_opener/config.json` |

> **從 v1.0.0 升級：** macOS 設定檔路徑已從 `~/.file_tab_opener.json` 變更。遷移方式：
> ```bash
> mv ~/.file_tab_opener.json ~/Library/Application\ Support/FileTabOpener/config.json
> ```

## 日誌

應用程式在終端輸出運作狀態（`INFO` 等級），並在日誌檔案中記錄詳細日誌（`DEBUG` 等級）。日誌檔案會自動輪替（上限 1MB，保留 3 個備份）。

| 輸出 | 等級 | 用途 |
|------|------|------|
| 終端 (stderr) | INFO 以上 | 啟動進度、操作結果 |
| 日誌檔案 | DEBUG 以上 | 疑難排解用的詳細記錄 |

日誌檔案位置：

| OS | 路徑 |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\debug.log` |
| macOS | `~/Library/Logs/FileTabOpener/debug.log` |
| Linux | `~/.local/share/FileTabOpener/debug.log` |

## 開發

```bash
# 開發用安裝（可編輯模式）
pip install -e .[all,dev]

# 執行測試
pytest tests/ -v
```

## 建構獨立應用程式

您可以使用 [PyInstaller](https://pyinstaller.org/) 建構獨立的 `.app`（macOS）或 `.exe`（Windows）。個人使用無需程式碼簽章。

```bash
# 安裝 PyInstaller
pip install pyinstaller

# 建構（在目標 OS 上執行）
pyinstaller --noconfirm --onedir --windowed \
    --collect-all customtkinter \
    --name "File Tab Opener" \
    file_tab_opener/__main__.py
```

輸出位於 `dist/File Tab Opener/`。macOS 會產生 `.app` 套件，Windows 會產生 `.exe` 資料夾。

> **注意：** 各 OS 的建構必須在該 OS 上進行。macOS 無法產生 Windows 的 `.exe`，反之亦然。

## 專案結構

```
file_tab_opener/
├── pyproject.toml           # 套件設定
├── LICENSE                  # MIT 授權
├── README.md                # 英文 README
├── README_zh_TW.md          # 本檔案
├── file_tab_opener/         # 原始碼套件
│   ├── __init__.py
│   ├── __main__.py          # 進入點
│   ├── config.py            # 設定檔管理
│   ├── i18n.py              # 國際化（5 種語言）
│   ├── gui.py               # 重新匯出模組（向下相容）
│   ├── widgets.py           # 元件抽象化（CTk / ttk）+ TabView
│   ├── history.py           # 歷史區段 UI
│   ├── tab_group.py         # 分頁群組區段 UI
│   ├── main_window.py       # 主視窗組成
│   ├── opener_win.py        # Windows 檔案總管分頁開啟
│   └── opener_mac.py        # macOS Finder 分頁開啟
└── tests/
    ├── test_config.py       # 設定模組測試
    ├── test_i18n.py         # i18n 模組測試
    ├── test_gui.py          # GUI 邏輯測試
    ├── test_opener_mac.py   # macOS opener 測試
    └── test_opener_win.py   # Windows opener 測試
```

## 授權

[MIT License](LICENSE) © 2026 obott9
