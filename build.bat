@echo off
echo ============================================
echo   RTCM Decoder - Build Script
echo ============================================
echo.

:: Check if PyInstaller is available
python -m PyInstaller --version >nul 2>&1
if %errorlevel% neq 0 (
    echo [*] Installing PyInstaller...
    pip install pyinstaller
    echo.
)

echo [*] Building RTCM Decoder...
echo.

python -m PyInstaller ^
    --onefile ^
    --name rtcm_decoder ^
    --distpath "..\dist" ^
    --workpath "..\build" ^
    --specpath ".." ^
    --clean ^
    --noconfirm ^
    src\main.py

if %errorlevel% equ 0 (
    echo.
    echo ============================================
    echo   Build OK!
    echo   Executable: dist\rtcm_decoder.exe
    echo ============================================
) else (
    echo.
    echo [!] Build failed.
)
pause
