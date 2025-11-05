# Automation Tools

업무 자동화를 위한 Python GUI 도구 모음

## 프로젝트 구조

```
automation-tools/
├── main_gui.py          # 메인 GUI (모든 도구 연결)
├── requirements.txt     # 공통 의존성
├── README.md
├── tools/               # 도구 모듈 디렉토리
│   ├── __init__.py      # 도구 등록 시스템
│   └── renamer/         # 파일명 변경 도구
│       ├── __init__.py
│       └── gui.py

```

## 설치 방법

```bash
pip install -r requirements.txt
```

## 사용 방법

```bash
python main_gui.py
```

메인 GUI가 실행되면 등록된 도구 목록이 표시됩니다. 원하는 도구를 클릭하면 해당 도구의 GUI가 팝업으로 열립니다.

## 프로젝트 목록

- **renamer**: 파일명 일괄 변경 도구

## 새로운 도구 추가하기

1. `tools/` 디렉토리 아래에 새 도구 디렉토리 생성 (예: `tools/my_tool/`)
2. `tools/my_tool/__init__.py` 파일 생성:
```python
from tools import ToolInfo, register_tool
from tools.my_tool.gui import MyToolWindow

MY_TOOL_INFO = ToolInfo(
    name="내 도구",
    description="도구 설명",
)

class MyTool:
    def create_widget(self, parent=None):
        window = MyToolWindow(parent)
        return window

# 자동 등록됨 (tools/__init__.py에서 import 시)
```
3. `tools/my_tool/gui.py`에 GUI 구현 (QMainWindow 또는 QWidget 상속)

## 개발 환경

- Python 3.x
- PySide6 (GUI 프레임워크)

