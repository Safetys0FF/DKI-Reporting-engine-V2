@echo off
setlocal EnableDelayedExpansion

REM -----------------------------------------------------------------------------
REM  Central Command Launcher
REM  Supports GUI (default) or runtime mode:  DKI_ENGINE_LAUNCHER.bat [gui|runtime]
REM -----------------------------------------------------------------------------

set "SCRIPT_DIR=%~dp0"
for %%I in ("%SCRIPT_DIR%..") do set "START_MENU_DIR=%%~fI"
for %%I in ("%START_MENU_DIR%..") do set "COMMAND_CENTER_DIR=%%~fI"
for %%I in ("%COMMAND_CENTER_DIR%..") do set "ROOT_DIR=%%~fI"

set "UI_DIR=%COMMAND_CENTER_DIR%\UI"
set "RUNTIME_DIR=%COMMAND_CENTER_DIR%\Start Menu\Run Time"
set "GUI_ENTRY=%UI_DIR%\gui_main_application.py"
set "RUNTIME_ENTRY=%RUNTIME_DIR%\main_application.py"

set "LAUNCH_MODE=GUI"
if /I "%~1"=="runtime" set "LAUNCH_MODE=RUNTIME"
if /I "%~1"=="--runtime" set "LAUNCH_MODE=RUNTIME"
if /I "%~1"=="gui" set "LAUNCH_MODE=GUI"

if /I "%LAUNCH_MODE%"=="GUI" (
    set "ENTRY_DIR=%UI_DIR%"
    set "ENTRY_SCRIPT=%GUI_ENTRY%"
) else (
    set "ENTRY_DIR=%RUNTIME_DIR%"
    set "ENTRY_SCRIPT=%RUNTIME_ENTRY%"
)

if not exist "%ENTRY_DIR%" (
    echo ERROR: Central Command directory missing: %ENTRY_DIR%
    endlocal & exit /b 1
)

if not exist "%ENTRY_SCRIPT%" (
    echo ERROR: Entry script not found: %ENTRY_SCRIPT%
    endlocal & exit /b 1
)

set "PYTHON="
for %%P in ("%RUNTIME_DIR%\venv\Scripts\python.exe" "%ROOT_DIR%\.venv\Scripts\python.exe" "%ROOT_DIR%\venv\Scripts\python.exe") do (
    if exist "%%~P" (
        set "PYTHON=%%~P"
        goto python_found
    )
)

for %%I in (python.exe py.exe) do (
    for /f "usebackq tokens=*" %%J in (where %%I 2^>nul) do (
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
