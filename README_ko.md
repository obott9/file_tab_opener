# File Tab Opener

[English](README.md) | [日本語](README_ja.md) | **한국어** | [繁體中文](README_zh_TW.md) | [简体中文](README_zh_CN.md)

여러 폴더를 **Windows 탐색기** 또는 **macOS Finder**의 하나의 창에서 탭으로 한번에 여는 GUI 도구입니다.

폴더를 하나씩 여는 대신, 이름이 지정된 탭 그룹에 등록하고 클릭 한 번으로 모두 열 수 있습니다. 각 폴더가 같은 창 내의 개별 탭으로 표시됩니다.

## 기능

- **탭 그룹 관리** — 이름이 지정된 그룹(예: "업무", "개인")을 만들고 폴더 경로를 등록
- **탭 그룹 복사** — 기존 탭 그룹을 복제. 복사 이름은 `"{기본이름} {번호}"` 형식(반각 공백 + 일련번호): "업무" → "업무 1" → "업무 2". 번호가 있는 탭의 복사는 기본 이름을 추출("업무 3" → 기본 "업무")하고 사용 가능한 번호를 할당. 하이픈 등의 구분자는 이름의 일부로 취급("업무-3" → "업무-3 1").
- **원클릭 열기** — 그룹 내 모든 폴더를 탐색기/Finder의 하나의 창에서 탭으로 열기
- **기록 & 고정** — 최근 열었던 폴더를 자동 기록, 자주 사용하는 항목은 고정
- **크로스 플랫폼** — Windows(탐색기 탭, Win 11 이상) 및 macOS(Finder 탭) 지원
- **듀얼 테마** — [customtkinter](https://github.com/TomSchimansky/CustomTkinter)로 모던한 UI. 미설치 시 표준 tkinter로 폴백
- **다국어 지원** — 영어, 일본어, 한국어, 번체 중국어, 간체 중국어(시스템 로케일에서 자동 감지)

## 요구 사항

- Python 3.10 이상
- Windows 11 이상 또는 macOS 12 이상

## 설치

```bash
git clone https://github.com/obott9/file_tab_opener.git
cd file_tab_opener
pip install .
```

모든 선택적 의존성을 포함한 설치(권장):

```bash
pip install .[all]
```

### 선택적 의존성 패키지

| 패키지 | 용도 | 설치 |
|--------|------|------|
| customtkinter | 모던 테마 GUI | `pip install .[ui]` |
| pywinauto | 탐색기 탭 자동화(Windows) | `pip install .[windows]` |

## 사용법

```bash
file-tab-opener
```

Python 모듈로 실행:

```bash
python -m file_tab_opener
```

### 빠른 시작

1. 앱 실행
2. **+ 탭 추가**를 클릭하여 탭 그룹 생성(예: "프로젝트 A")
3. 텍스트 입력란, **찾아보기** 버튼 또는 탐색기에서 경로 붙여넣기로 폴더 경로 추가
4. **탭으로 열기**를 클릭하여 모든 폴더를 하나의 창에서 탭으로 열기

### 기록 섹션

- 콤보박스에 폴더 경로를 입력/붙여넣기하고 **열기** 클릭
- 경로는 자동으로 기록에 저장
- **Pin**으로 목록 상단에 고정
- **Clear**로 고정 외의 기록을 모두 삭제

## 작동 방식

### Windows(탐색기 탭)

호환성을 극대화하는 3단계 폴백:

1. **pywinauto UIA** — 새 탐색기 창을 열고 UI Automation으로 연결. UIA InvokePattern("+" 버튼)으로 새 탭을 만들고 UIA ValuePattern으로 주소 표시줄에 경로를 직접 설정. Enter 전송에는 PostMessage(창 지정, 글로벌 아님)를 사용. UIA 작업 실패 시에만 키보드 단축키로 폴백. 입력 후 경로를 검증하고 실패 시 자동 재시도. 가장 신뢰성 높은 방식.
2. **ctypes SendInput** — Win32 `SendInput` API를 사용한 동일한 키 입력 방식. 외부 의존성 없음. 포커스 및 타이밍 문제로 신뢰성이 다소 낮음.
3. **개별 창** — `subprocess`로 각 폴더를 개별 탐색기 창으로 여는 폴백.

### macOS(Finder 탭)

2단계 폴백:

1. **AppleScript + System Events** — 첫 번째 폴더를 Finder에서 열고 ⌘T 키 입력으로 새 탭을 만들어 AppleScript로 각 탭의 대상을 설정.
2. **개별 창** — `open` 명령으로 개별 창으로 여는 폴백.

> **참고:** AppleScript 방식에는 손쉬운 사용 권한이 필요합니다. **시스템 설정 → 개인정보 보호 및 보안 → 손쉬운 사용**에서 Terminal.app(또는 사용 중인 터미널)을 허용하세요.

### 성능에 대해(Windows)

Windows 탐색기에는 탭 조작용 공개 API가 없습니다. 모든 방식이 UI 자동화 또는 키 입력 전송(`Ctrl+T` → 주소 표시줄 입력)에 의존하며, 탭마다 UI 응답을 기다리는 `delay`가 필요합니다. UIA ValuePattern을 통한 주소 표시줄 직접 입력, 대기 시간 최소화, 불필요한 단계 생략 등 가능한 한 고속화를 적용했지만, 네이티브 탭 API가 존재하지 않는 이상 이것이 현재의 한계입니다. 탭 수가 많을 경우, macOS(Finder는 AppleScript로 직접 탭 조작 가능)에 비해 확연히 느려집니다.

> **⚠️ 주의(ctypes SendInput 폴백):** 탭을 여는 동안 키보드나 마우스를 조작하지 마세요. ctypes 폴백 방식은 OS 수준의 키 입력 전송(`SendInput`)을 사용하므로, 작업 중 입력이 자동화 처리를 방해할 수 있습니다. pywinauto UIA 방식은 주로 대상 지정 UI Automation과 PostMessage(글로벌 키 입력 없음)를 사용하지만, UIA 작업 실패 시 키보드 단축키로 폴백할 수 있습니다.

## 설정 파일

설정은 JSON 파일에 저장됩니다:

| OS | 경로 |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\config.json` |
| macOS | `~/Library/Application Support/FileTabOpener/config.json` |
| Linux | `~/.config/file_tab_opener/config.json` |

> **v1.0.0에서 업그레이드:** macOS 설정 파일 경로가 `~/.file_tab_opener.json`에서 변경되었습니다. 마이그레이션:
> ```bash
> mv ~/.file_tab_opener.json ~/Library/Application\ Support/FileTabOpener/config.json
> ```

## 로그

앱은 터미널에 동작 상황(`INFO` 레벨)을 출력하고, 로그 파일에 상세 로그(`DEBUG` 레벨)를 기록합니다. 로그 파일은 자동 로테이션(최대 1MB, 3세대 보관)됩니다.

| 출력 | 레벨 | 용도 |
|------|------|------|
| 터미널 (stderr) | INFO 이상 | 시작 상황, 작업 결과 |
| 로그 파일 | DEBUG 이상 | 문제 해결용 상세 기록 |

로그 파일 위치:

| OS | 경로 |
|----|------|
| Windows | `%APPDATA%\FileTabOpener\debug.log` |
| macOS | `~/Library/Logs/FileTabOpener/debug.log` |
| Linux | `~/.local/share/FileTabOpener/debug.log` |

## 개발

```bash
# 개발용 설치(편집 가능 모드)
pip install -e .[all,dev]

# 테스트 실행
pytest tests/ -v
```

## 독립형 앱 빌드

[PyInstaller](https://pyinstaller.org/)를 사용하여 독립형 `.app`(macOS) 또는 `.exe`(Windows)를 빌드할 수 있습니다. 개인 사용이라면 코드 서명이 필요 없습니다.

```bash
# PyInstaller 설치
pip install pyinstaller

# 빌드(빌드 대상 OS에서 실행)
pyinstaller --noconfirm --onedir --windowed \
    --collect-all customtkinter \
    --name "File Tab Opener" \
    file_tab_opener/__main__.py
```

출력은 `dist/File Tab Opener/`에 생성됩니다. macOS에서는 `.app` 번들, Windows에서는 `.exe` 폴더가 생성됩니다.

> **참고:** 각 OS용 빌드는 해당 OS에서 수행해야 합니다. macOS에서 Windows용 `.exe`를 만들 수 없습니다(반대도 마찬가지).

## 프로젝트 구조

```
file_tab_opener/
├── pyproject.toml           # 패키지 설정
├── LICENSE                  # MIT 라이선스
├── README.md                # 영어 README
├── README_ko.md             # 이 파일
├── file_tab_opener/         # 소스 패키지
│   ├── __init__.py
│   ├── __main__.py          # 진입점
│   ├── config.py            # 설정 파일 관리
│   ├── i18n.py              # 국제화 (5개 언어)
│   ├── gui.py               # 재내보내기 모듈 (하위 호환)
│   ├── widgets.py           # 위젯 추상화 (CTk / ttk) + TabView
│   ├── history.py           # 기록 섹션 UI
│   ├── tab_group.py         # 탭 그룹 섹션 UI
│   ├── main_window.py       # 메인 윈도우 구성
│   ├── opener_win.py        # Windows 탐색기 탭 열기
│   └── opener_mac.py        # macOS Finder 탭 열기
└── tests/
    ├── test_config.py       # 설정 모듈 테스트
    ├── test_i18n.py         # i18n 모듈 테스트
    ├── test_gui.py          # GUI 로직 테스트
    ├── test_opener_mac.py   # macOS opener 테스트
    └── test_opener_win.py   # Windows opener 테스트
```

## 라이선스

[MIT License](LICENSE) © 2026 obott9
