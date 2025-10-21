@echo off
REM Unified Diagnostic System - Windows Launcher
REM AUTO-DETECTION MODE: Automatically detects system state and switches modes
REM - JOIN MODE: System running - connects to existing bus (no new bus creation)
REM - SAFE MODE: System down - creates ONE bus and initializes full system

echo ========================================
echo UNIFIED DIAGNOSTIC SYSTEM LAUNCHER
echo AUTO-DETECTION MODE
echo ========================================
echo.
echo FIXED: Single bus instance - no more multiple bus creation
echo.
echo MODES (AUTO-DETECTED):
echo   JOIN MODE - System running - connects to existing bus
echo   SAFE MODE - System down - creates ONE bus for all modules
echo.
echo Usage:
echo   LAUNCH_DIAGNOSTIC_SYSTEM.bat [options]
echo.
echo Options:
echo   --smoke        Run smoke baseline test
echo   --test         Run in test mode
echo   --log-level    Set logging level (DEBUG, INFO, WARNING, ERROR)
echo.
echo Examples:
echo   LAUNCH_DIAGNOSTIC_SYSTEM.bat
echo   LAUNCH_DIAGNOSTIC_SYSTEM.bat --smoke
echo   LAUNCH_DIAGNOSTIC_SYSTEM.bat --test
echo.

REM Change to the script directory
cd /d "%~dp0"

REM Set Python path
set PYTHONPATH=%CD%;%CD%\..;%CD%\..\..\Bus Core Design;%CD%\..\..\..\..;%PYTHONPATH%

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

echo ========================================
echo AUTO-DETECTING SYSTEM STATE...
echo ========================================
echo.
echo The system will automatically detect:
echo   - JOIN MODE if system is running
echo   - SAFE MODE if system needs initialization
echo.

REM Launch the diagnostic system (auto-detects mode)
python core.py %*

REM Check exit code
if errorlevel 1 (
    echo.
    echo ERROR: Diagnostic system failed to launch or encountered an error
    echo Check logs in: library\system_logs\
    pause
    exit /b 1
) else (
    echo.
    echo Diagnostic system shutdown complete
)

pause
