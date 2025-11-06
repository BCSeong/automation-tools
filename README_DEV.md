# 업무 자동화 도구 - 개발자 문서

이 문서는 개발자를 위한 프로젝트 구조와 개발 환경 설정 방법을 설명합니다.

## 프로젝트 구조

```
automation-tools/
├── main_gui.py          # 메인 GUI (모든 도구 연결)
├── requirements.txt     # Python 의존성
├── build.spec           # PyInstaller 빌드 설정
├── build.bat            # Windows 빌드 스크립트
├── README.md            # 사용자용 문서
├── README_DEV.md        # 개발자용 문서 (이 파일)
└── tools/               # 도구 모듈 디렉토리
    ├── __init__.py      # 도구 등록 시스템
    └── renamer/         # 파일명 변경 도구
        ├── __init__.py  # 도구 등록 정보
        └── gui.py       # GUI 구현
```

## 개발 환경 설정

### 1. Python 설치

- Python 3.8 이상 필요
- [Python 공식 사이트](https://www.python.org/downloads/)에서 다운로드

### 2. 가상 환경 생성 (권장)

```bash
# 가상 환경 생성
python -m venv venv

# Windows에서 활성화
venv\Scripts\activate


### 3. 의존성 설치

```bash
pip install -r requirements.txt
```

### 4. 개발용 추가 의존성 (선택사항)

EXE 빌드를 위해 PyInstaller가 필요합니다:

```bash
pip install pyinstaller
```

## 실행 방법

### 개발 모드

```bash
python main_gui.py
```

### EXE 빌드

#### 방법 1: 빌드 스크립트 사용 (권장)

```bash
build.bat
```

#### 방법 2: PyInstaller 직접 실행

```bash
pyinstaller build.spec
```

빌드 완료 후 `dist/automation-tools.exe` 파일이 생성됩니다.

#### 빌드 옵션 수정

`build.spec` 파일을 수정하여 다음을 변경할 수 있습니다:

- **아이콘 추가**: `icon='path/to/icon.ico'` 추가
- **콘솔 창 표시**: `console=True`로 변경 (디버깅용)
- **파일명 변경**: `name='원하는이름'` 수정

## 새로운 도구 추가하기

### 1. 도구 디렉토리 생성

```bash
mkdir tools\my_tool
```

### 2. GUI 구현

`tools/my_tool/gui.py` 파일 생성:

```python
from __future__ import annotations
from PySide6.QtWidgets import QMainWindow, QLabel, QVBoxLayout, QWidget

class MyToolWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("내 도구")
        
        central = QWidget(self)
        self.setCentralWidget(central)
        
        layout = QVBoxLayout(central)
        label = QLabel("내 도구 GUI")
        layout.addWidget(label)
```

### 3. 도구 등록

`tools/my_tool/__init__.py` 파일 생성:

```python
from __future__ import annotations
from tools import ToolInfo
from tools.my_tool.gui import MyToolWindow

__all__ = ["MyTool", "MY_TOOL_INFO"]

MY_TOOL_INFO = ToolInfo(
    name="내 도구",
    description="도구에 대한 간단한 설명",
    icon=None,  # 아이콘 파일 경로 (선택사항)
)

class MyTool:
    """내 도구 클래스"""
    
    def create_widget(self, parent=None):
        """GUI 윈도우 생성"""
        window = MyToolWindow(parent)
        window.resize(800, 600)
        return window
```

### 4. 자동 등록

`tools/__init__.py`의 `_register_all_tools()` 함수에 추가:

```python
def _register_all_tools():
    # ... 기존 도구 등록 ...
    
    # 새 도구 등록
    try:
        from tools.my_tool import MyTool, MY_TOOL_INFO
        register_tool("my_tool", MY_TOOL_INFO, MyTool)
    except ImportError:
        pass
```

### 5. 테스트

```bash
python main_gui.py
```

메인 GUI에서 새 도구가 표시되는지 확인합니다.

## 코드 구조 설명

### 도구 등록 시스템 (`tools/__init__.py`)

- **ToolInfo**: 도구의 메타데이터 (이름, 설명, 아이콘)
- **register_tool()**: 도구를 시스템에 등록
- **get_registered_tools()**: 등록된 모든 도구 목록 반환
- **create_tool_widget()**: 도구 ID로 GUI 생성

### 메인 GUI (`main_gui.py`)

- 등록된 모든 도구를 버튼으로 표시
- 도구 클릭 시 `create_tool_widget()`을 호출하여 팝업 GUI 생성
- 각 도구는 독립적인 윈도우로 실행됨

### 도구 구현 패턴

각 도구는 다음을 만족해야 합니다:

1. `QMainWindow` 또는 `QWidget`을 상속한 GUI 클래스
2. `ToolInfo` 객체로 메타데이터 정의
3. `create_widget(parent)` 메서드를 가진 도구 클래스
4. `tools/__init__.py`에서 자동 등록

## 디버깅

### 콘솔 출력 확인

EXE 빌드 시 콘솔을 표시하려면 `build.spec`에서:

```python
console=True,  # False -> True로 변경
```

### 로그 추가

필요한 경우 Python `logging` 모듈 사용:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 빌드 문제 해결

### PyInstaller 관련 오류

1. **ModuleNotFoundError**: `hiddenimports`에 누락된 모듈 추가
2. **파일 크기 문제**: `upx=True`로 압축 활성화 (기본값)
3. **실행 오류**: `console=True`로 변경하여 오류 메시지 확인

### PySide6 관련 오류

PySide6가 제대로 포함되지 않으면 `build.spec`의 `hiddenimports`에 추가:

```python
hiddenimports=[
    'PySide6.QtCore',
    'PySide6.QtGui',
    'PySide6.QtWidgets',
    # ... 기타 필요한 모듈
],
```

## 테스트

### 단위 테스트 (향후 구현)

```bash
pytest tests/
```

### 수동 테스트 체크리스트

- [ ] 메인 GUI 실행 확인
- [ ] 모든 도구 버튼 표시 확인
- [ ] 각 도구 팝업 정상 작동 확인
- [ ] EXE 빌드 후 실행 확인

## 버전 관리

### Git 사용 권장

```bash
git init
git add .
git commit -m "Initial commit"
```

### .gitignore 예시

```
# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
venv/
env/

# Build
build/
dist/
*.spec.bak

# IDE
.vscode/
.idea/
*.swp
*.swo

# OS
.DS_Store
Thumbs.db
```

## 기여 방법

1. 새 기능이나 버그 수정을 위한 브랜치 생성
2. 변경사항 구현 및 테스트
3. Pull Request 생성


