# File Tab Opener

[English](README.md) | **日本語** | [한국어](README_ko.md) | [繁體中文](README_zh_TW.md) | [简体中文](README_zh_CN.md)

複数のフォルダを **Windows Explorer** または **macOS Finder** の1つのウィンドウにタブとして一括で開くGUIツールです。

フォルダを1つずつ開く代わりに、名前付きのタブグループに登録してワンクリックで開けます。各フォルダが同じウィンドウ内の個別タブとして表示されます。

## 機能

- **タブグループ管理** — 名前付きグループ（例: 「仕事」「プライベート」）を作成し、フォルダパスを登録
- **タブグループ複製** — 既存のタブグループを複製。複製名は `"{ベース名} {番号}"` 形式（半角スペース＋連番）: 「仕事」→「仕事 1」→「仕事 2」。番号付きタブの複製はベース名を抽出（「仕事 3」→ ベース「仕事」）し、空き番号を採番。ハイフン等の区切りは名前の一部として扱う（「仕事-3」→「仕事-3 1」）。
- **ワンクリックオープン** — グループ内の全フォルダをExplorer/Finderの1ウィンドウにタブで開く
- **履歴 & ピン留め** — 最近開いたフォルダを自動記録、よく使うものはピン留め
- **クロスプラットフォーム** — Windows（Explorerタブ、Win 11以降）とmacOS（Finderタブ）対応
- **デュアルテーマ** — [customtkinter](https://github.com/TomSchimansky/CustomTkinter) でモダンなUI。未インストール時は標準tkinterにフォールバック。
  ※ Windowsでは一部の標準tkinter/ttkコントロール（スクロールバー、ネイティブダイアログ等）がダークテーマに完全対応しません。これはWindowsのttkテーマエンジンがダークモード非対応のためです。
- **多言語対応** — 英語・日本語・韓国語・繁体字中国語・簡体字中国語（システムロケールから自動検出）

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

1. **pywinauto UIA** — 新しいExplorerウィンドウを開き、UI Automationで接続。UIA InvokePattern（「+」ボタン）で新しいタブを作成し、UIA ValuePatternでアドレスバーにパスを直接設定。Enterの送信にはPostMessage（ウィンドウ指定、グローバルではない）を使用。UIA操作失敗時のみキーボードショートカットにフォールバック。入力後にパスを検証し、失敗時は自動リトライ。最も信頼性が高い方式。
2. **ctypes SendInput** — Win32 `SendInput` APIを使った同様のキーストローク方式。外部依存なし。フォーカスやタイミングの問題で信頼性はやや低い。
3. **個別ウィンドウ** — `subprocess` で各フォルダを個別のExplorerウィンドウで開くフォールバック。

### macOS（Finderタブ）

2段階フォールバック:

1. **AppleScript + System Events** — 最初のフォルダをFinderで開き、⌘Tキーストロークで新しいタブを作成、AppleScriptで各タブのターゲットを設定。
2. **個別ウィンドウ** — `open` コマンドで個別ウィンドウとして開くフォールバック。

> **注意:** AppleScript方式にはアクセシビリティ権限が必要です。**システム設定 → プライバシーとセキュリティ → アクセシビリティ** でTerminal.app（またはお使いのターミナル）を許可してください。

### パフォーマンスについて（Windows）

Windows Explorerにはタブ操作用の公開APIがありません。すべての方式がUIオートメーションまたはキーストローク送信（`Ctrl+T` → アドレスバー入力）に依存しており、タブごとにUIの応答を待つ `delay` が必要です。UIA ValuePatternによるアドレスバー直接入力、待機時間の最小化、不要な手順の省略など、可能な限りの高速化を施していますが、ネイティブのタブAPIが存在しない以上、これが現状の限界です。タブ数が多い場合、macOS（FinderはAppleScriptで直接タブ操作可能）に比べて明らかに遅くなります。

> **⚠️ 注意（ctypes SendInput フォールバック）:** タブを開いている最中はキーボードやマウスを操作しないでください。ctypes フォールバック方式はOSレベルのキーストローク送信（`SendInput`）を使用しているため、操作中の入力が自動化処理に干渉する可能性があります。pywinauto UIA 方式は主にターゲット指定のUIオートメーションとPostMessage（グローバルキーストロークなし）を使用しますが、UIA操作失敗時はキーボードショートカットにフォールバックする場合があります。

### ネットワークパス（Windows）

UNCパス（`\\server\share`）に対応しています。ネットワーク共有はExplorerのみが認証ダイアログを表示できるため、UNCパスは通常の `is_dir()` バリデーションをスキップし、Explorerに直接渡されます。

認証が必要なUNCパスの場合:
1. Explorerが「Windowsセキュリティ」の資格情報入力ダイアログを表示
2. アプリは認証の完了を待たずにタブ作成処理を完了
3. タブには一時的に「PC」が表示される
4. ユーザーが認証を通すと、Explorerが実際のネットワーク共有に遷移

認証ダイアログをキャンセルした場合、タブは「PC」のまま残ります。

## 設定ファイル

設定はJSONファイルに保存されます:

| OS | パス |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\config.json` |
| macOS | `~/Library/Application Support/FileTabOpener/config.json` |

> **v1.0.0からのアップグレード:** macOSの設定ファイルパスが `~/.file_tab_opener.json` から変更されました。移行するには:
> ```bash
> mv ~/.file_tab_opener.json ~/Library/Application\ Support/FileTabOpener/config.json
> ```

## ログ

アプリはターミナルに動作状況（`INFO`レベル）を出力し、ログファイルに詳細ログ（`DEBUG`レベル）を記録します。ログファイルは自動ローテーション（上限1MB、3世代保持）されます。

| 出力先 | レベル | 用途 |
|--------|--------|------|
| ターミナル (stderr) | INFO以上 | 起動状況、操作結果 |
| ログファイル | DEBUG以上 | トラブルシューティング用の詳細記録 |

ログファイルの場所:

| OS | パス |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\debug.log` |
| macOS | `~/Library/Logs/FileTabOpener/debug.log` |

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
├── CHANGELOG.md             # バージョン履歴
├── requirements.txt         # 依存関係一覧（非推奨；pyproject.toml推奨）
├── README.md                # 英語版README
├── README_ja.md             # このファイル
├── README_ko.md             # 韓国語版README
├── README_zh_TW.md          # 繁體中文版README
├── README_zh_CN.md          # 简体中文版README
├── file_tab_opener/         # ソースパッケージ
│   ├── __init__.py
│   ├── __main__.py          # エントリーポイント
│   ├── config.py            # 設定ファイル管理
│   ├── i18n.py              # 国際化（5言語対応）
│   ├── gui.py               # 再エクスポートモジュール（後方互換）
│   ├── widgets.py           # ウィジェット抽象化（CTk / ttk）+ TabView
│   ├── history.py           # 履歴セクションUI
│   ├── tab_group.py         # タブグループセクションUI
│   ├── main_window.py       # メインウィンドウ構成
│   ├── opener_win.py        # Windows Explorerタブ開き処理
│   └── opener_mac.py        # macOS Finderタブ開き処理
└── tests/
    ├── test_config.py       # 設定モジュールのテスト
    ├── test_i18n.py         # i18nモジュールのテスト
    ├── test_gui.py          # GUIロジックのテスト
    ├── test_opener_mac.py   # macOS openerのテスト
    └── test_opener_win.py   # Windows openerのテスト
```

## 関連プロジェクト

- **[FileTabOpenerM](https://github.com/obott9/FileTabOpenerM)** — macOS ネイティブ版（Swift/SwiftUI）。AX API + AppleScript ハイブリッドで Finder タブを確実に制御。モダンサイドバーレイアウト搭載。
- **[FileTabOpenerW](https://github.com/obott9/FileTabOpenerW)** — Windows ネイティブ版（C++/Win32）。UI Automation による Explorer タブの直接制御。

## ライセンス

[MIT License](LICENSE) © 2026 obott9
