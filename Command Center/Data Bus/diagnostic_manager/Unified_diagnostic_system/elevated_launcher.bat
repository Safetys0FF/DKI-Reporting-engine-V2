@echo off
echo ============================================================
echo UNIFIED DIAGNOSTIC SYSTEM - ELEVATED LAUNCHER
echo ============================================================
echo.
echo This launcher will run the diagnostic system with elevated privileges
echo to ensure full access to all system directories.
echo.
echo WARNING: This requires Administrator privileges.
echo.

REM Check if running as administrator
net session >nul 2>&1
if %errorLevel% == 0 (
    echo [SUCCESS] Running with Administrator privileges
    echo.
) else (
    echo [ERROR] This script must be run as Administrator
    echo.
    echo Please right-click this file and select "Run as administrator"
    echo.
    pause
    exit /b 1
)

REM Set working directory
cd /d "%~dp0"

REM Set Python path for elevated execution
set PYTHONPATH=%CD%;%CD%\..;%CD%\..\..;%CD%\..\..\Bus Core Design

REM Launch with elevated privileges
echo [INFO] Launching Unified Diagnostic System with elevated privileges...
echo [INFO] Working Directory: %CD%
echo [INFO] Python Path: %PYTHONPATH%
echo.

python main_launcher.py --test-mode

echo.
echo [INFO] Diagnostic system execution completed
pause
