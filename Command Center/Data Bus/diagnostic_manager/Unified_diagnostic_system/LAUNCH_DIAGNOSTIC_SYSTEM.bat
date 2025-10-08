@echo off
REM Unified Diagnostic System - Windows Launcher
REM This batch file launches the main diagnostic system

echo ========================================
echo UNIFIED DIAGNOSTIC SYSTEM LAUNCHER
echo ========================================
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Set Python path
set PYTHONPATH=%CD%;%CD%\..;%CD%\..\..\Bus Core Design;%PYTHONPATH%

echo Working Directory: %CD%
echo Python Path: %PYTHONPATH%
echo.

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python is not installed or not in PATH
    echo Please install Python and ensure it's in your system PATH
    pause
    exit /b 1
)

REM Launch the main launcher
echo Launching Unified Diagnostic System...
echo.
python main_launcher.py %*

REM Check exit code
if errorlevel 1 (
    echo.
    echo ERROR: Diagnostic system failed to launch or encountered an error
    pause
) else (
    echo.
    echo Diagnostic system shutdown complete
)

pause
