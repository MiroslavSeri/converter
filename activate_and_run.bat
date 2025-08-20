@echo off
setlocal

REM 1) Vytvoř venv, pokud ještě neexistuje
if not exist "venv\Scripts\python.exe" (
    echo [*] Creating virtual environment...
    python -m venv venv
    if not exist "venv\Scripts\python.exe" (
        echo [!] Failed to create venv. >&2
        exit /b 1
    )
)

REM 2) Aktivuj venv
call "venv\Scripts\activate.bat"

REM 3) Ověř, jaký Python běží (pro kontrolu)
for /f "delims=" %%i in ('python -c "import sys; print(sys.executable)"') do set PYEXE=%%i
echo [*] Using Python: %PYEXE%

REM 4) Aktualizuj pip a nainstaluj závislosti do venv
python -m pip install --upgrade pip
if exist "requirements.txt" (
    echo [*] Installing dependencies from requirements.txt...
    python -m pip install -r requirements.txt || (
        echo [!] Failed to install requirements. >&2
        exit /b 1
    )
) else (
    echo [!] requirements.txt not found – skipping.
)

endlocal
exit /b %EXITCODE%
