@echo off
setlocal EnableDelayedExpansion

REM -----------------------------------------------------------------------------
REM  DKI Central Command Launcher ? GUI (default) or runtime mode
REM -----------------------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
for %%I in ("%~dp0..") do set "START_MENU_DIR=%%~fI"
for %%I in ("%START_MENU_DIR%\..") do set "COMMAND_CENTER_DIR=%%~fI"
for %%I in ("%COMMAND_CENTER_DIR%\..") do set "ROOT_DIR=%%~fI"

set "RUNTIME_DIR=%COMMAND_CENTER_DIR%\Start Menu\Run Time"
set "RUNTIME_ENTRY=%RUNTIME_DIR%\main_application.py"

REM Central Command UI location (primary interface)
set "MODERN_GUI_DIR=%COMMAND_CENTER_DIR%\UI"
set "GUI_ENTRY=%MODERN_GUI_DIR%\gui_main_application.py"
set "PYTHONPATH=%COMMAND_CENTER_DIR%;%COMMAND_CENTER_DIR%\UI;%COMMAND_CENTER_DIR%\Mission Debrief;%COMMAND_CENTER_DIR%\Mission Debrief\The Librarian;%COMMAND_CENTER_DIR%\Mission Debrief\Debrief\README;%COMMAND_CENTER_DIR%\Data Bus;%COMMAND_CENTER_DIR%\Data Bus\Bus Core Design;%ROOT_DIR%\The Warden;%ROOT_DIR%\Evidence Locker;%ROOT_DIR%\The Marshall;%ROOT_DIR%\The War Room\Processors"

if not exist "%GUI_ENTRY%" (
    echo ERROR: Central Command UI not found at %GUI_ENTRY%
    echo Ensure the Central Command repository is present at %ROOT_DIR% before launching.
    endlocal & exit /b 1
)

set "LAUNCH_MODE=GUI"
if /I "%~1"=="runtime" set "LAUNCH_MODE=RUNTIME"
if /I "%~1"=="--runtime" set "LAUNCH_MODE=RUNTIME"
if /I "%~1"=="gui" set "LAUNCH_MODE=GUI"

if /I "%LAUNCH_MODE%"=="GUI" (
    set "ENTRY_DIR=%MODERN_GUI_DIR%"
    set "ENTRY_SCRIPT=%GUI_ENTRY%"
) else (
    set "ENTRY_DIR=%RUNTIME_DIR%"
    set "ENTRY_SCRIPT=%RUNTIME_ENTRY%"
)

if not exist "%ENTRY_DIR%" (
    echo ERROR: Entry directory missing: %ENTRY_DIR%
    endlocal & exit /b 1
)

if not exist "%ENTRY_SCRIPT%" (
    echo ERROR: Entry script not found: %ENTRY_SCRIPT%
    endlocal & exit /b 1
)

REM -----------------------------------------------------------------------------
REM  Processor / OCR dependency bootstrap
REM -----------------------------------------------------------------------------
set "PROCESSOR_ROOT=%ROOT_DIR%\The War Room\Processors"
set "POPPLER_BIN=%PROCESSOR_ROOT%\poppler-25.07.0\Library\bin"
if exist "%POPPLER_BIN%" (
    set "PATH=%POPPLER_BIN%;%PATH%"
    set "POPPLER_PATH=%POPPLER_BIN%"
)
set "FFMPEG_BIN=%PROCESSOR_ROOT%\ffmpeg-2025-09-18-git-c373636f55-essentials_build\bin"
if exist "%FFMPEG_BIN%" (
    set "PATH=%FFMPEG_BIN%;%PATH%"
)
set "TESSERACT_CMD="
for %%T in ("C:\Program Files\Tesseract-OCR\tesseract.exe" "C:\Program Files (x86)\Tesseract-OCR\tesseract.exe" "%PROCESSOR_ROOT%\tesseract.exe") do (
    if exist "%%~T" (
        set "TESSERACT_CMD=%%~T"
        set "PATH=%%~dpT;%PATH%"
        if exist "%%~dpTtessdata" set "TESSDATA_PREFIX=%%~dpTtessdata"
        goto tess_ready
    )
)
:tess_ready
REM If a bundled tessdata exists and no prefix set, fall back to it
if not defined TESSDATA_PREFIX if exist "%PROCESSOR_ROOT%\tessdata" set "TESSDATA_PREFIX=%PROCESSOR_ROOT%\tessdata"

set "PYTHON="
for %%P in ("%RUNTIME_DIR%\venv\Scripts\python.exe" "%ROOT_DIR%\.venv\Scripts\python.exe" "%ROOT_DIR%\venv\Scripts\python.exe") do (
    if exist "%%~P" (
        set "PYTHON=%%~P"
        goto python_found
    )
)

for %%I in (python.exe py.exe) do (
    for /f "tokens=*" %%J in ('where %%I 2^>nul') do (
        if not defined PYTHON (
            set "PYTHON=%%~J"
            goto python_found
        )
    )
)

:python_found
if not defined PYTHON (
    echo ERROR: Unable to locate a Python interpreter.
    echo Install Python 3.10+ or activate the Central Command virtual environment.
    endlocal & exit /b 1
)

pushd "%ENTRY_DIR%" >nul 2>&1
if errorlevel 1 (
    echo ERROR: Unable to change directory to %ENTRY_DIR%
    endlocal & exit /b 1
)

echo ============================================================================
echo                  DKI Central Command - %LAUNCH_MODE% Launcher
echo ============================================================================
echo Using Python : %PYTHON%
echo Entry Script : %ENTRY_SCRIPT%
echo.
if /I "%LAUNCH_MODE%"=="GUI" (
    echo Starting GUI application...
) else (
    echo Starting runtime controller...
)
echo.

"%PYTHON%" "%ENTRY_SCRIPT%"
set "EXIT_CODE=%ERRORLEVEL%"

popd >nul 2>&1

if not "%EXIT_CODE%"=="0" (
    echo.
    echo Application exited with error code %EXIT_CODE%.
    echo Review the console output for details.
)

echo.
echo Central Command session ended.
pause
endlocal & exit /b %EXIT_CODE%







