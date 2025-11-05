# 빌드 명령어 가이드

## Windows CMD에서 빌드

### 방법 1: build.spec 파일 사용 (권장)

```cmd
pyinstaller build.spec
```

### 방법 2: 직접 명령어 사용

```cmd
pyinstaller --onefile --noconsole --name automation-tools main_gui.py
```

옵션 설명:
- `--onefile`: 단일 EXE 파일로 생성
- `--noconsole`: 콘솔 창 숨김 (GUI 애플리케이션)
- `--name`: 생성될 EXE 파일명

### 방법 3: 추가 옵션 포함

```cmd
pyinstaller --onefile --noconsole --name automation-tools --hidden-import PySide6.QtCore --hidden-import PySide6.QtGui --hidden-import PySide6.QtWidgets --hidden-import tools --hidden-import tools.renamer --hidden-import tools.renamer.gui main_gui.py
```

## Linux/Mac Bash에서 빌드

### 방법 1: build.spec 파일 사용 (권장)

```bash
pyinstaller build.spec
```

### 방법 2: 직접 명령어 사용

```bash
pyinstaller --onefile --noconsole --name automation-tools main_gui.py
```

## 빌드 결과

빌드 완료 후:
- **Windows**: `dist\automation-tools.exe`
- **Linux/Mac**: `dist/automation-tools`

## 빌드 전 확인사항

1. PyInstaller 설치 확인:
```cmd
pip install pyinstaller
```

2. 현재 디렉토리 확인:
```cmd
cd D:\OneDrive - KohYoung\mygit\automation-tools
```

## 빠른 빌드 (일반적인 경우)

가장 간단한 명령어:

```cmd
pyinstaller build.spec
```

또는:

```cmd
pyinstaller --onefile --noconsole --name automation-tools main_gui.py
```

## 디버깅 모드 (콘솔 창 표시)

오류 확인이 필요할 때:

```cmd
pyinstaller --onefile --console --name automation-tools main_gui.py
```

`--noconsole` 대신 `--console` 사용

