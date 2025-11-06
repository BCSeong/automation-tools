@echo off
REM Automation Tools EXE Build Script

echo ==========================================
echo Building Automation Tools
echo ==========================================
echo.

REM Check PyInstaller installation
python -c "import PyInstaller" 2>nul
if errorlevel 1 (
    echo PyInstaller is not installed.
    echo Installing PyInstaller...
    pip install pyinstaller
    if errorlevel 1 (
        echo PyInstaller installation failed!
        pause
        exit /b 1
    )
)

echo.
echo Building...
echo.

REM Clean previous build artifacts
if exist build rmdir /s /q build
if exist dist rmdir /s /q dist
if exist automation-tools.spec del /q automation-tools.spec

REM Run PyInstaller
pyinstaller build.spec

if errorlevel 1 (
    echo.
    echo Build failed!
    pause
    exit /b 1
)

echo.
echo ==========================================
echo Build complete!
echo ==========================================
echo.
echo EXE file location: dist\automation-tools.exe
echo.
pause

