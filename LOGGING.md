# 로깅 가이드

이 문서는 프로젝트에서 로깅을 사용하는 방법을 설명합니다.

## 중요: 로그 메시지는 영문으로 작성

**모든 로그 메시지는 반드시 영문으로 작성해야 합니다.**
**템플릿 파일과 모든 문서의 로그 예제도 영문으로 작성되어 있습니다.**

## 로그 파일 저장 위치

### 자동 결정 로직

로그 파일 저장 위치는 실행 모드에 따라 자동으로 결정됩니다:

1. **EXE 모드** (배포된 실행 파일):
   - 위치: `실행파일과_같은_디렉토리/logs/`
   - 예: `D:/automation-tools/automation-tools.exe` → `D:/automation-tools/logs/`

2. **개발 모드** (Python 스크립트 실행):
   - 위치: `프로젝트_루트/logs/`
   - 예: `automation-tools/logs/`

### 로그 파일명 형식

기본 파일명 형식: `YYYY-MM-DD_tool-name.log`

- 예: `2025-11-06_tools.renamer.log`
- 날짜별로 자동 분리되어 관리됩니다.

## 사용 방법

### 1. 간편 함수 사용 (권장)

도구별 로거를 간단하게 생성:

```python
from tools.common.log_utils import get_tool_logger

# 도구별 로거 생성
logger = get_tool_logger("renamer")

# 로그 기록 (모든 로그 메시지는 영문으로 작성)
logger.info("Renaming task started")
logger.debug("Debug info: %s", some_value)
logger.warning("Warning: %s", warning_message)
logger.error("Error occurred: %s", error_message)
```

### 2. 고급 설정 사용

더 세밀한 제어가 필요한 경우:

```python
from tools.common.log_utils import setup_logger
from tools.common.log_utils import get_log_directory
import logging

# 커스텀 로거 설정
logger = setup_logger(
    name="my_custom_logger",
    log_file="custom.log",  # 파일명 지정 (상대 경로는 logs/ 기준)
    level=logging.DEBUG,    # 로그 레벨
    format_string="%(asctime)s - %(levelname)s - %(message)s"  # 커스텀 포맷
)

# 로그 디렉토리 확인
log_dir = get_log_directory()
print(f"Log directory: {log_dir}")
```

### 3. Worker 클래스에서 사용

Pipeline의 Worker 클래스에서 로깅:

```python
from tools.common.log_utils import get_tool_logger

class MyToolWorker(QObject):
    def __init__(self, ...):
        super().__init__()
        self.logger = get_tool_logger("my_tool")
    
    def run(self):
        try:
            self.logger.info("Task started")
            # 작업 수행
            self.logger.debug("Processing: %s", item)
            self.logger.info("Task completed: %d items processed", count)
        except Exception as e:
            self.logger.error("Task failed: %s", str(e), exc_info=True)
            self.failed.emit(str(e))
```

### 4. GUI에서 사용

GUI에서도 로깅을 사용할 수 있습니다:

```python
from tools.common.log_utils import get_tool_logger

class MyToolWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_tool_logger("my_tool")
        # ...
    
    def _on_run(self):
        self.logger.info("User clicked run button")
        # 작업 수행
```

## 로그 레벨

Python logging 모듈의 표준 로그 레벨을 사용합니다:

- **DEBUG**: 상세한 디버깅 정보
- **INFO**: 일반적인 정보 메시지 (작업 시작, 완료 등)
- **WARNING**: 경고 메시지 (기본 동작에는 영향 없음)
- **ERROR**: 오류 메시지 (기능이 실패함)
- **CRITICAL**: 심각한 오류 (프로그램이 계속 실행 불가능할 수 있음)

```python
import logging

logger = get_tool_logger("my_tool", level=logging.DEBUG)  # 모든 레벨 기록
logger = get_tool_logger("my_tool", level=logging.INFO)   # INFO 이상만 기록 (기본값)
```

## 로그 포맷

기본 포맷: `%(asctime)s - %(name)s - %(levelname)s - %(message)s`

예시 출력:
```
2025-11-06 20:30:45 - tools.renamer - INFO - Renaming task started: folder=/path/to/folder, pattern=*.bmp
2025-11-06 20:30:46 - tools.renamer - DEBUG - Processing: file001.bmp
2025-11-06 20:30:47 - tools.renamer - INFO - Task completed: 10/10 files processed successfully
```

### 커스텀 포맷

```python
logger = setup_logger(
    name="my_tool",
    format_string="[%(levelname)s] %(asctime)s - %(message)s"
)
# 출력: [INFO] 2025-11-06 20:30:45 - Task started
```

## 예외 정보 기록

예외 발생 시 상세 정보를 기록하려면 `exc_info=True` 사용:

```python
try:
    # 작업 수행
    pass
except Exception as e:
    logger.error("Task failed", exc_info=True)
    # 스택 트레이스가 로그에 포함됨
```

## 로그 파일 관리

### 로그 파일 크기 제한

현재는 날짜별로 자동 분리되지만, 필요시 로그 로테이션을 추가할 수 있습니다:

```python
from logging.handlers import RotatingFileHandler

# 예시: 10MB 이상이면 로테이션 (최대 5개 파일 보관)
handler = RotatingFileHandler(
    log_file,
    maxBytes=10*1024*1024,  # 10MB
    backupCount=5,
    encoding='utf-8'
)
```

### 로그 파일 정리

오래된 로그 파일은 수동으로 삭제하거나 스크립트로 자동 정리할 수 있습니다.

## 모범 사례

### 1. 적절한 로그 레벨 사용

```python
# ❌ 나쁜 예
logger.info("Variable value: %s", debug_value)  # DEBUG 레벨이 적절

# ✅ 좋은 예
logger.debug("Variable value: %s", debug_value)  # 디버깅 정보
logger.info("Task started")                     # 일반 정보
logger.warning("Warning message")                # 경고
logger.error("Error occurred")                  # 오류
```

### 2. 구조화된 메시지

```python
# ❌ 나쁜 예
logger.info(f"File {file} processed, total {count}")

# ✅ 좋은 예
logger.info("File processed: file=%s, count=%d", file, count)
# 또는
logger.info("File processed", extra={"file": file, "count": count})
```

### 3. 민감한 정보 제외

```python
# ❌ 나쁜 예
logger.info("User login: password=%s", password)

# ✅ 좋은 예
logger.info("User login: username=%s", username)
```

### 4. Worker에서 로깅

```python
class MyToolWorker(QObject):
    def __init__(self, ...):
        self.logger = get_tool_logger("my_tool")
    
    def run(self):
        self.logger.info("Task started")
        try:
            # 작업 수행
            for item in items:
                self.logger.debug("Processing: %s", item)
                # 처리 로직
            self.logger.info("Task completed: %d items processed", len(items))
            self.finished.emit(len(items), len(items))
        except Exception as e:
            self.logger.error("Task failed: %s", str(e), exc_info=True)
            self.failed.emit(str(e))
```

### 5. GUI와 로그 파일 동시 사용

GUI의 로그 위젯과 파일 로깅을 함께 사용:

```python
class MyToolWindow(QMainWindow):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.logger = get_tool_logger("my_tool")
        # GUI 로그 위젯에도 표시
        self.logger.addHandler(self._create_gui_handler())
    
    def _create_gui_handler(self):
        """GUI 로그 위젯용 핸들러"""
        class GuiLogHandler(logging.Handler):
            def __init__(self, widget):
                super().__init__()
                self.widget = widget
            
            def emit(self, record):
                msg = self.format(record)
                self.widget.appendPlainText(msg)
        
        return GuiLogHandler(self.log)
```

## 문제 해결

### 로그 파일이 생성되지 않음

1. `logs/` 디렉토리 권한 확인
2. 디스크 공간 확인
3. 로그 레벨이 너무 높게 설정되지 않았는지 확인

### 로그 파일이 너무 큼

1. 날짜별로 자동 분리되므로 하루치 로그만 기록
2. 필요시 로그 로테이션 설정 추가
3. 오래된 로그 파일 정리

### 로그가 중복으로 기록됨

- 같은 로거에 여러 핸들러가 추가되었을 수 있음
- `setup_logger()`는 중복 핸들러를 방지하지만, 수동으로 추가한 경우 확인 필요

## 참고

- [Python logging 공식 문서](https://docs.python.org/3/library/logging.html)
- [logging 모범 사례](https://docs.python.org/3/howto/logging.html#logging-basic-tutorial)

