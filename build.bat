@echo off
REM 업무 자동화 도구 EXE 빌드 스크립트

echo ==========================================
echo 업무 자동화 도구 빌드 시작
echo ==========================================
echo.

REM PyInstaller 설치 확인
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller가 설치되어 있지 않습니다.
    echo 설치 중...
    pip install pyinstaller
    if errorlevel 1 (
        echo PyInstaller 설치 실패!
        pause
        exit /b 1
    )
)

echo.
echo 빌드 중...
echo.

REM 기존 빌드 결과물 정리
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist automation-tools.spec del /q automation-tools.spec

REM PyInstaller 실행
pyinstaller build.spec

if errorlevel 1 (
    echo.
    echo 빌드 실패!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo 빌드 완료!
echo ==========================================
echo.
echo EXE 파일 위치: dist\automation-tools.exe
echo.
pause

