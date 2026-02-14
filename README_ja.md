# File Tab Opener

[English README](README.md)

複数のフォルダを **Windows Explorer** または **macOS Finder** の1つのウィンドウにタブとして一括で開くGUIツールです。

フォルダを1つずつ開く代わりに、名前付きのタブグループに登録してワンクリックで開けます。各フォルダが同じウィンドウ内の個別タブとして表示されます。

## 機能

- **タブグループ管理** — 名前付きグループ（例: 「仕事」「プライベート」）を作成し、フォルダパスを登録
- **ワンクリックオープン** — グループ内の全フォルダをExplorer/Finderの1ウィンドウにタブで開く
- **履歴 & ピン留め** — 最近開いたフォルダを自動記録、よく使うものはピン留め
- **クロスプラットフォーム** — Windows（Explorerタブ、Win 11以降）とmacOS（Finderタブ）対応
- **デュアルテーマ** — [customtkinter](https://github.com/TomSchimansky/CustomTkinter) でモダンなUI。未インストール時は標準tkinterにフォールバック
- **多言語対応** — 英語・日本語UI（システムロケールから自動検出）

## 動作要件

- Python 3.10以上
- Windows 11以上 または macOS 12以上

## インストール

```bash
git clone https://github.com/obott9/file_tab_opener.git
cd file_tab_opener
pip install .
```

オプション依存を含む全機能インストール（推奨）:

```bash
pip install .[all]
```

### オプション依存パッケージ

| パッケージ | 用途 | インストール |
|-----------|------|------------|
| customtkinter | モダンテーマGUI | `pip install .[ui]` |
| pywinauto | Explorerタブ自動化（Windows） | `pip install .[windows]` |

## 使い方

```bash
file-tab-opener
```

Pythonモジュールとして実行:

```bash
python -m file_tab_opener
```

### クイックスタート

1. アプリを起動
2. **+ タブ追加** をクリックしてタブグループを作成（例: 「プロジェクトA」）
3. テキスト入力欄、**参照** ボタン、またはExplorerからのパス貼り付けでフォルダパスを追加
4. **タブで開く** をクリックして全フォルダを1ウィンドウにタブで開く

### 履歴セクション

- コンボボックスにフォルダパスを入力/貼り付けて **開く** をクリック
- パスは自動的に履歴に保存
- **Pin** でリストの上部に固定
- **Clear** でピン留め以外の履歴を全削除

## 仕組み

### Windows（Explorerタブ）

互換性を最大化する3段階フォールバック:

1. **pywinauto UIA** — 新しいExplorerウィンドウを開き、UI Automationで接続。Ctrl+Tで新しいタブを作成し、UIA ValuePatternでアドレスバーにパスを直接設定。最も信頼性が高い方式。
2. **ctypes SendInput** — Win32 `SendInput` APIを使った同様のキーストローク方式。外部依存なし。フォーカスやタイミングの問題で信頼性はやや低い。
3. **個別ウィンドウ** — `subprocess` で各フォルダを個別のExplorerウィンドウで開くフォールバック。

### macOS（Finderタブ）

2段階フォールバック:

1. **AppleScript + System Events** — 最初のフォルダをFinderで開き、⌘Tキーストロークで新しいタブを作成、AppleScriptで各タブのターゲットを設定。
2. **個別ウィンドウ** — `open` コマンドで個別ウィンドウとして開くフォールバック。

> **注意:** AppleScript方式にはアクセシビリティ権限が必要です。**システム設定 → プライバシーとセキュリティ → アクセシビリティ** でTerminal.app（またはお使いのターミナル）を許可してください。

## 設定ファイル

設定はJSONファイルに保存されます:

| OS | パス |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\config.json` |
| macOS | `~/.file_tab_opener.json` |
| Linux | `~/.config/file_tab_opener/config.json` |

## ログ

アプリはターミナルに動作状況（`INFO`レベル）を出力し、ログファイルに詳細ログ（`DEBUG`レベル）を記録します。

| 出力先 | レベル | 用途 |
|--------|--------|------|
| ターミナル (stderr) | INFO以上 | 起動状況、操作結果 |
| ログファイル | DEBUG以上 | トラブルシューティング用の詳細記録 |

ログファイルの場所:

| OS | パス |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\debug.log` |
| macOS | `~/Library/Logs/FileTabOpener/debug.log` |
| Linux | `~/.local/share/FileTabOpener/debug.log` |

## 開発

```bash
# 開発用インストール（編集可能モード）
pip install -e .[all,dev]

# テスト実行
pytest tests/ -v
```

## スタンドアロンアプリのビルド

[PyInstaller](https://pyinstaller.org/) を使って、スタンドアロンの `.app`（macOS）または `.exe`（Windows）をビルドできます。個人利用ならコード署名は不要です。

```bash
# PyInstallerをインストール
pip install pyinstaller

# ビルド（ビルド対象のOS上で実行）
pyinstaller --noconfirm --onedir --windowed \
    --collect-all customtkinter \
    --name "File Tab Opener" \
    file_tab_opener/__main__.py
```

出力先は `dist/File Tab Opener/`。macOSでは `.app` バンドル、Windowsでは `.exe` フォルダが生成されます。

> **注意:** 各OS用のビルドはそのOS上で行う必要があります。macOSからWindows用 `.exe` を作ることはできません（逆も同様）。

## プロジェクト構成

```
file_tab_opener/
├── pyproject.toml           # パッケージ設定
├── LICENSE                  # MITライセンス
├── README.md                # 英語版README
├── README_ja.md             # このファイル
├── file_tab_opener/         # ソースパッケージ
│   ├── __init__.py
│   ├── __main__.py          # エントリーポイント
│   ├── config.py            # 設定ファイル管理
│   ├── i18n.py              # 国際化（英語/日本語）
│   ├── gui.py               # GUI（customtkinter / tkinter）
│   ├── opener_win.py        # Windows Explorerタブ開き処理
│   └── opener_mac.py        # macOS Finderタブ開き処理
└── tests/
    ├── test_config.py       # 設定モジュールのテスト（40テスト）
    └── test_i18n.py         # i18nモジュールのテスト（18テスト）
```

## ライセンス

[MIT License](LICENSE) © 2026 obott9
