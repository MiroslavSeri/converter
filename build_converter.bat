@echo off
setlocal

REM ===== 1. Aktivace virtuálního prostředí =====
if not exist "venv\Scripts\activate.bat" (
    echo [*] Vytvářím venv...
    python -m venv venv
)
call venv\Scripts\activate.bat

REM ===== 2. Instalace PyInstalleru =====
pip show pyinstaller >nul 2>&1
if errorlevel 1 (
    echo [*] Instalace PyInstaller...
    python -m pip install pyinstaller
)

REM ===== 3. Build EXE =====
echo [*] Spouštím build...
pyinstaller --onefile ^
    --name converter ^
    --add-binary "ffmpeg.exe;." ^
    --add-binary "mediainfo.exe;." ^
    BatchConverter.py

REM ===== 4. Výsledek =====
echo.
echo [✅] Hotovo! Spustitelný soubor najdeš v dist\converter.exe
pause
endlocal
