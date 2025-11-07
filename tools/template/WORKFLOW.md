# 도구 개발 워크플로우

이 문서는 Designer 기반 도구 개발의 3단계 파이프라인을 설명합니다.

## 개발 파이프라인

### 1단계: 기능 개발 및 CLI 테스트

**목표**: 비즈니스 로직을 구현하고 CLI로 테스트

#### 작업 내용

1. **functions.py 작성**
   - 도구 전용 함수 구현 (순수 함수)
   - CLI 테스트 지원 (`if __name__ == "__main__"`)

2. **pipeline.py 작성**
   - Worker 클래스 작성 (연산 Pipeline)
   - common 함수들과 도구 전용 함수 조합
   - CLI 테스트 지원 (`if __name__ == "__main__"`)

3. **constants.json 작성**
   - GUI 표시값과 메서드명 매핑 정의

4. **CLI 테스트**
   ```bash
   # functions.py 직접 실행
   python tools/my_tool/functions.py --test example_function --param1 test
   
   # pipeline.py 직접 실행 (Worker 테스트)
   python tools/my_tool/pipeline.py --input data.txt
   ```

#### 예시: constants.json (매핑만)

```json
{
  "example_mode": {
    "display": ["모드 1", "모드 2"],
    "mapping": {
      "모드 1": "method1",
      "모드 2": "method2"
    }
  }
}
```

### 2단계: GUI 디자인 (PySide6 Designer)

**목표**: Designer로 UI 레이아웃 및 기본값 설정

#### 작업 내용

1. **Designer 실행**
   ```bash
   pyside6-designer
   ```

2. **ui/main.ui 파일 생성**
   - Designer에서 새 MainWindow 생성
   - 필요한 위젯 배치
   - **중요**: 각 위젯의 `objectName` 설정 (Python에서 접근하기 위해)

3. **기본값 설정**
   - Designer의 Property Editor에서 각 위젯의 기본값 설정
   - 예: QLineEdit의 `text`, QSpinBox의 `value`, QCheckBox의 `checked` 등
   - **GUI 기본값은 모두 Designer에서 설정** (config.json 아님)

4. **저장**
   - `tools/my_tool/ui/main.ui`로 저장

#### Designer 사용 팁

- **objectName 설정**: 모든 위젯에 의미있는 objectName 설정
  - 예: `btn_run`, `edit_input`, `log`, `progress`
- **기본값 설정**: Property Editor에서 직접 설정
- **레이아웃**: 적절한 Layout 사용 (QVBoxLayout, QHBoxLayout 등)

### 3단계: GUI와 기능 통합

**목표**: .ui 파일을 로드하고 core와 연결

#### 작업 내용

1. **gui.py 작성**
   - `load_ui_file()`로 .ui 파일 로드 (공통 유틸리티 사용)
   - Designer에서 설정한 기본값이 자동 적용됨
   - constants.json 로드 및 ComboBox 항목 설정

2. **시그널-슬롯 연결**
   ```python
   # Designer에서 설정한 objectName 사용
   self.btn_run.clicked.connect(self._on_run)
   self.edit_input.textChanged.connect(self._on_input_changed)
   ```

3. **Worker 연결**
   - GUI 값 → 메서드명 매핑 (constants.json 사용)
   - Pipeline에 매핑된 메서드명 전달
   - 시그널-슬롯 연결

4. **테스트**
   ```bash
   # GUI 테스트
   python tools/my_tool/gui.py
   
   # 또는 메인 GUI에서 테스트
   python main_gui.py
   ```

## 파일 구조

```
tools/my_tool/
├── __init__.py          # 도구 등록
├── functions.py         # 도구 전용 함수 (CLI 테스트 지원)
├── pipeline.py          # 연산 Pipeline (Worker, CLI 테스트 지원)
├── gui.py               # GUI 통합 (.ui 로드)
├── constants.json       # GUI 표시값 <-> 메서드명 매핑
└── ui/
    └── main.ui          # Designer 파일
```

## 설정 분리 원칙

### constants.json에 포함
- ✅ GUI 표시값과 메서드명 매핑
- ✅ 예: {"display": ["모드 1"], "mapping": {"모드 1": "method1"}}

### Designer (.ui 파일)에 포함
- ✅ GUI 기본값 (text, value, checked 등)
- ✅ 레이아웃 구조
- ✅ 위젯 배치
- ✅ 윈도우 크기, 제목

### 메시지
- ✅ 모든 메시지(경고, 오류, 정보)는 GUI 코드에 하드코딩

## 예시: 전체 워크플로우

### 1단계: 기능 개발

```python
# functions.py
def process_data(input_path: str, threshold: int) -> int:
    """데이터 처리"""
    # 비즈니스 로직
    return processed_count

# pipeline.py
class MyToolWorker(QObject):
    def __init__(self, method_name: str, ...):
        self.method_name = method_name
    
    def run(self):
        if self.method_name == "method1":
            result = process_data(...)
```

### 2단계: GUI 디자인

1. Designer에서 `ui/main.ui` 생성
2. QLineEdit 추가 (objectName: `edit_input`)
3. QPushButton 추가 (objectName: `btn_run`)
4. Property Editor에서 기본값 설정:
   - `edit_input.text`: "기본 입력값"
   - `btn_run.text`: "실행"

### 3단계: 통합

```python
# gui.py
from tools.common.ui_utils import load_ui_file

def _load_ui(self):
    ui_path = Path(__file__).parent / 'ui' / 'main.ui'
    load_ui_file(ui_path, self)  # 공통 유틸리티 사용
    # Designer에서 설정한 기본값을 self 로 호출 가능

def _connect(self):
    self.btn_run.clicked.connect(self._on_run)

def _start_worker(self):
    # GUI 값 → 메서드명 매핑
    mode_display = self.combo_mode.currentText()
    method_name = self.constants.get('example_mode', {}).get('mapping', {}).get(mode_display, 'method1')
    
    self.worker = MyToolWorker(
        method_name=method_name,  # 매핑된 메서드명 전달
        input_path=self.edit_input.text(),
    )
```

## 빌드 시 주의사항

EXE 빌드 시 .ui 파일이 포함되도록 `build.spec` 확인:

```python
datas=[
    ('tools/*/ui/*.ui', 'tools'),
],
```

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

