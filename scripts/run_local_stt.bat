@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "PROJECT_DIR=%SCRIPT_DIR%.."
pushd "%PROJECT_DIR%"

if not exist ".venv\Scripts\Activate.bat" (
    echo Virtual environment was not found at ".venv\Scripts\Activate.bat".
    echo Create it first with:
    echo   python -m venv .venv
    echo   .venv\Scripts\Activate.ps1
    echo   pip install -e .
    popd
    exit /b 1
)

call ".venv\Scripts\Activate.bat"
if errorlevel 1 (
    echo Failed to activate the virtual environment.
    popd
    exit /b 1
)

if "%~1"=="" (
    echo Starting guided mode...
    local-stt-diarization --guided
) else (
    local-stt-diarization %*
)

set "EXIT_CODE=%ERRORLEVEL%"
popd
exit /b %EXIT_CODE%
