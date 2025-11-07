# 도구 템플릿 사용 가이드

이 템플릿을 사용하여 새로운 도구를 빠르게 생성할 수 있습니다.

## 빠른 시작

### 1. 새 도구 디렉토리 생성

```bash
mkdir tools\my_tool
mkdir tools\my_tool\ui
```

### 2. 템플릿 파일 복사

템플릿 파일들을 새 도구 디렉토리로 복사합니다:

```bash
copy tools\template\__init__.py.template tools\my_tool\__init__.py
copy tools\template\functions.py.template tools\my_tool\functions.py
copy tools\template\pipeline.py.template tools\my_tool\pipeline.py
copy tools\template\gui.py.template tools\my_tool\gui.py
copy tools\template\constants.json.template tools\my_tool\constants.json
```

### 3. 템플릿 변수 치환

파일 내의 다음 변수들을 실제 값으로 치환:

- `{{TOOL_ID}}`: 도구 ID (예: `my_tool`)
- `{{TOOL_NAME}}`: 도구 이름 (예: `My Tool`)
- `{{TOOL_CLASS}}`: 클래스 이름 (예: `MyTool`)
- `{{TOOL_CLASS_UPPER}}`: 대문자 클래스 이름 (예: `MY_TOOL`)
- `{{TOOL_DISPLAY_NAME}}`: 표시 이름 (예: `내 도구`)
- `{{TOOL_DESCRIPTION}}`: 도구 설명

### 4. 도구 등록

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

## 개발 워크플로우

자세한 내용은 [WORKFLOW.md](WORKFLOW.md)를 참고하세요.

### 3단계 파이프라인

1. **기능 개발**: `pipeline.py`, `function` 에서 비즈니스 로직 구현 및 CLI 테스트
2. **GUI 디자인**: PySide6 Designer로 `ui/main.ui` 생성
3. **통합**: `gui.py`에서 .ui 로드 및 core와 연결

## 파일 구조

```
tools/my_tool/
├── __init__.py          # 도구 등록
├── functions.py         # 도구 전용 함수 (CLI 테스트 지원)
├── pipeline.py          # 연산 Pipeline (Worker 클래스, CLI 테스트 지원)
├── gui.py               # GUI 통합 (.ui 로드)
├── constants.json       # GUI 표시값 <-> 메서드명 매핑
└── ui/
    └── main.ui          # Designer 파일
```

## 설정 분리 원칙

### constants.json
- GUI 표시값과 메서드명 매핑
- 예: {"display": ["모드 1", "모드 2"], "mapping": {"모드 1": "method1"}}

### Designer (.ui 파일)
- GUI 기본값 (text, value, checked 등)
- 레이아웃 구조
- 위젯 배치
- 윈도우 크기, 제목

### 메시지
- 모든 메시지(경고, 오류, 정보)는 GUI 코드에 하드코딩

## Designer 사용

### Designer 실행

```bash
pyside6-designer
```

### 주요 작업

1. 새 MainWindow 생성
2. 위젯 배치 및 레이아웃 설정
3. **중요**: 각 위젯의 `objectName` 설정 (Python에서 접근)
4. Property Editor에서 기본값 설정
5. `ui/main.ui`로 저장

### objectName 예시

- 버튼: `btn_run`, `btn_clear`
- 입력 필드: `edit_input`, `edit_output`
- 로그: `log`
- 진행률: `progress`

## 테스트

### CLI 테스트

```bash
# functions.py 직접 실행
python tools/my_tool/functions.py --test example_function --param1 test --param2 10

# pipeline.py 직접 실행 (Worker 테스트)
python tools/my_tool/pipeline.py --input data.txt
```

### GUI 테스트

```bash
# GUI 단독 테스트
python tools/my_tool/gui.py

# 메인 GUI에서 테스트
python main_gui.py
```

## 공통 유틸리티 사용

프로젝트의 공통 함수들은 `tools/common/`에 있습니다:

- `tools.common.file_utils`: 파일 관련 함수 (ensure_write, list_files)
- `tools.common.path_utils`: 경로 관련 함수 (natural_sort_key)
- `tools.common.ui_utils`: UI 관련 함수 (load_ui_file)

```python
from tools.common.file_utils import list_files
from tools.common.ui_utils import load_ui_file
```

## 참고

- **renamer 도구**: 실제 구현 예제 참고
- **템플릿**: Designer 기반 방식 (권장)

## 문제 해결

### .ui 파일을 찾을 수 없음
- `ui/main.ui` 파일이 존재하는지 확인
- 경로가 올바른지 확인

### 위젯을 찾을 수 없음
- Designer에서 objectName이 올바르게 설정되었는지 확인
- Python 코드에서 objectName이 일치하는지 확인

### 기본값이 적용되지 않음
- Designer의 Property Editor에서 기본값이 설정되었는지 확인
- .ui 파일을 다시 저장

