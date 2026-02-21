# File Tab Opener

[English](README.md) | [日本語](README_ja.md) | [한국어](README_ko.md) | [繁體中文](README_zh_TW.md) | **简体中文**

一个 GUI 工具，用于在 **Windows 资源管理器** 或 **macOS Finder** 的单个窗口中以标签页方式一次性打开多个文件夹。

无需逐个打开文件夹，只需将它们注册到命名的标签组中，一键即可全部打开——每个文件夹会显示为同一窗口中的独立标签页。

## 功能

- **标签组管理** — 创建命名组（例如"工作"、"个人"），并分配文件夹路径
- **标签组复制** — 复制现有的标签组。复制名称遵循 `"{基础名称} {编号}"` 格式（半角空格 + 序号）："工作" → "工作 1" → "工作 2"。复制带编号的标签会提取基础名称（"工作 3" → 基础 "工作"），并分配下一个可用编号。连字符等分隔符视为名称的一部分（"工作-3" → "工作-3 1"）。
- **一键打开** — 将组中的所有文件夹以标签页方式在资源管理器/Finder 的单个窗口中打开
- **历史记录 & 固定** — 自动记录最近打开的文件夹，常用项目可固定
- **跨平台** — 支持 Windows（资源管理器标签页，Win 11 以上）及 macOS（Finder 标签页）
- **双主题** — 使用 [customtkinter](https://github.com/TomSchimansky/CustomTkinter) 实现现代化 UI；未安装时回退至标准 tkinter
- **多语言** — 英文、日文、韩文、繁体中文、简体中文（从系统区域设置自动检测）

## 系统要求

- Python 3.10 以上
- Windows 11 以上或 macOS 12 以上

## 安装

```bash
git clone https://github.com/obott9/file_tab_opener.git
cd file_tab_opener
pip install .
```

包含所有可选依赖的完整安装（推荐）：

```bash
pip install .[all]
```

### 可选依赖包

| 包 | 用途 | 安装 |
|----|------|------|
| customtkinter | 现代主题 GUI | `pip install .[ui]` |
| pywinauto | 资源管理器标签页自动化（Windows） | `pip install .[windows]` |

## 使用方法

```bash
file-tab-opener
```

以 Python 模块运行：

```bash
python -m file_tab_opener
```

### 快速开始

1. 启动应用
2. 点击 **+ 添加标签** 创建标签组（例如"项目 A"）
3. 通过文本输入框、**浏览** 按钮或从资源管理器粘贴路径来添加文件夹路径
4. 点击 **以标签打开** 将所有文件夹以标签页方式在单个窗口中打开

### 历史记录区

- 在下拉框中输入/粘贴文件夹路径，点击 **打开**
- 路径会自动保存到历史记录
- 点击 **Pin** 将项目固定在列表顶部
- 点击 **Clear** 删除所有未固定的历史记录

## 工作原理

### Windows（资源管理器标签页）

三层回退机制以最大化兼容性：

1. **pywinauto UIA** — 打开新的资源管理器窗口，通过 UI Automation 连接。使用 Ctrl+T 创建新标签页，并通过 UIA ValuePattern 直接设置地址栏路径。输入后验证路径，失败时自动重试。最可靠的方式。
2. **ctypes SendInput** — 使用 Win32 `SendInput` API 的相同按键方式。无外部依赖，但因焦点和时序问题可靠性稍低。
3. **单独窗口** — 通过 `subprocess` 在单独的资源管理器窗口中打开各文件夹的回退方案。

### macOS（Finder 标签页）

两层回退机制：

1. **AppleScript + System Events** — 在 Finder 中打开第一个文件夹，然后通过 ⌘T 按键创建新标签页，以 AppleScript 设置各标签页的目标。
2. **单独窗口** — 使用 `open` 命令在单独窗口中打开的回退方案。

> **注意：** AppleScript 方式需要辅助功能权限。请前往 **系统设置 → 隐私与安全性 → 辅助功能**，并启用 Terminal.app（或您使用的终端）的访问权限。

### 性能说明（Windows）

Windows 资源管理器没有标签页操作的公开 API。所有方式都依赖 UI 自动化或按键模拟（`Ctrl+T` → 地址栏输入），每个标签页都需要等待 UI 响应的 `delay`。我们已通过 UIA ValuePattern 直接输入地址栏、最小化等待时间、省略不必要的步骤等方式尽可能优化，但由于不存在原生标签页 API，这是目前的根本限制。标签页数量多时，相比 macOS（Finder 支持通过 AppleScript 直接操作标签页）会明显较慢。

## 配置文件

设置存储在 JSON 文件中：

| OS | 路径 |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\config.json` |
| macOS | `~/Library/Application Support/FileTabOpener/config.json` |
| Linux | `~/.config/file_tab_opener/config.json` |

> **从 v1.0.0 升级：** macOS 配置文件路径已从 `~/.file_tab_opener.json` 变更。迁移方式：
> ```bash
> mv ~/.file_tab_opener.json ~/Library/Application\ Support/FileTabOpener/config.json
> ```

## 日志

应用在终端输出运行状态（`INFO` 级别），并在日志文件中记录详细日志（`DEBUG` 级别）。日志文件自动轮转（上限 1MB，保留 3 个备份）。

| 输出 | 级别 | 用途 |
|------|------|------|
| 终端 (stderr) | INFO 以上 | 启动进度、操作结果 |
| 日志文件 | DEBUG 以上 | 故障排查用的详细记录 |

日志文件位置：

| OS | 路径 |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\debug.log` |
| macOS | `~/Library/Logs/FileTabOpener/debug.log` |
| Linux | `~/.local/share/FileTabOpener/debug.log` |

## 开发

```bash
# 开发用安装（可编辑模式）
pip install -e .[all,dev]

# 运行测试
pytest tests/ -v
```

## 构建独立应用

您可以使用 [PyInstaller](https://pyinstaller.org/) 构建独立的 `.app`（macOS）或 `.exe`（Windows）。个人使用无需代码签名。

```bash
# 安装 PyInstaller
pip install pyinstaller

# 构建（在目标 OS 上运行）
pyinstaller --noconfirm --onedir --windowed \
    --collect-all customtkinter \
    --name "File Tab Opener" \
    file_tab_opener/__main__.py
```

输出位于 `dist/File Tab Opener/`。macOS 会生成 `.app` 包，Windows 会生成 `.exe` 文件夹。

> **注意：** 各 OS 的构建必须在该 OS 上进行。macOS 无法生成 Windows 的 `.exe`，反之亦然。

## 项目结构

```
file_tab_opener/
├── pyproject.toml           # 包配置
├── LICENSE                  # MIT 许可证
├── README.md                # 英文 README
├── README_zh_CN.md          # 本文件
├── file_tab_opener/         # 源码包
│   ├── __init__.py
│   ├── __main__.py          # 入口点
│   ├── config.py            # 配置文件管理
│   ├── i18n.py              # 国际化（5 种语言）
│   ├── gui.py               # 重新导出模块（向下兼容）
│   ├── widgets.py           # 组件抽象化（CTk / ttk）+ TabView
│   ├── history.py           # 历史区段 UI
│   ├── tab_group.py         # 标签组区段 UI
│   ├── main_window.py       # 主窗口组成
│   ├── opener_win.py        # Windows 资源管理器标签打开
│   └── opener_mac.py        # macOS Finder 标签打开
└── tests/
    ├── test_config.py       # 配置模块测试
    ├── test_i18n.py         # i18n 模块测试
    ├── test_gui.py          # GUI 逻辑测试
    ├── test_opener_mac.py   # macOS opener 测试
    └── test_opener_win.py   # Windows opener 测试
```

## 许可证

[MIT License](LICENSE) © 2026 obott9
