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
    ├── common/          # 공통 유틸리티
    │   ├── file_utils.py    # 파일 관련 함수
    │   ├── path_utils.py    # 경로 관련 함수
    │   └── ui_utils.py      # UI 관련 함수
    ├── renamer/         # 파일명 변경 도구 (예제)
    │   ├── __init__.py
    │   ├── functions.py     # 도구 전용 함수
    │   ├── pipeline.py      # 연산 Pipeline
    │   ├── gui.py           # GUI 구현
    │   ├── constants.json   # GUI 표시값 <-> 메서드명 매핑
    │   └── ui/
    │       └── main.ui      # Designer 파일
    └── template/        # 새 도구 생성용 템플릿
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

### 2. 템플릿 사용 (권장)

템플릿을 사용하여 빠르게 생성:

```bash
# 템플릿 파일 복사
copy tools\template\__init__.py.template tools\my_tool\__init__.py
copy tools\template\functions.py.template tools\my_tool\functions.py
copy tools\template\pipeline.py.template tools\my_tool\pipeline.py
copy tools\template\gui.py.template tools\my_tool\gui.py
copy tools\template\constants.json.template tools\my_tool\constants.json
```

템플릿 변수 치환: `{{TOOL_ID}}`, `{{TOOL_NAME}}`, `{{TOOL_CLASS}}` 등

자세한 내용은 `tools/template/README.md` 참고

### 3. 도구 등록

템플릿의 `__init__.py.template`을 사용하거나 직접 작성:

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
        # Designer에서 설정한 윈도우 크기가 자동 적용됨
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

### 공통 유틸리티 (`tools/common/`)

- **file_utils.py**: 파일 관련 범용 함수 (ensure_write, list_files)
- **path_utils.py**: 경로 관련 범용 함수 (natural_sort_key)
- **ui_utils.py**: UI 관련 범용 함수 (load_ui_file)

모든 도구에서 공통으로 사용 가능한 함수들입니다.

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

각 도구는 다음 구조를 따릅니다:

1. **functions.py**: 도구 전용 순수 함수 (CLI 테스트 지원)
2. **pipeline.py**: 연산 Pipeline (Worker 클래스, CLI 테스트 지원)
3. **gui.py**: GUI 구현 (Designer .ui 파일 로드)
4. **constants.json**: GUI 표시값 <-> 메서드명 매핑
5. **__init__.py**: 도구 등록 정보
6. **ui/main.ui**: Designer 파일

### 개발 워크플로우

자세한 내용은 `tools/template/WORKFLOW.md` 참고:

1. **기능 개발**: functions.py, pipeline.py 작성 및 CLI 테스트
2. **GUI 디자인**: Designer로 ui/main.ui 생성
3. **통합**: gui.py에서 UI 로드 및 Pipeline 연결

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


