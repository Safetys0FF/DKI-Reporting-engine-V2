@echo off
title DKI Engine - Uninstaller
color 0C
setlocal EnableDelayedExpansion

set "BASE_DRIVE=%~d0"
set "START_MENU=%~dp0"
set "REPORT_DIR=%BASE_DRIVE%\Report Engine"
set "VENV_DIR=%BASE_DRIVE%\dki_env"
set "DESKTOP=%USERPROFILE%\Desktop"
set "STARTMENU_DIR=%APPDATA%\Microsoft\Windows\Start Menu\Programs\DKI Engine"
set "INSTALL_FLAG=%REPORT_DIR%\installation.flag"

echo.
echo =============================================================================
echo                      DKI ENGINE - UNINSTALLATION SYSTEM
echo =============================================================================
echo.
echo WARNING: This will remove the DKI Engine runtime from drive %BASE_DRIVE%.
echo What will be removed:
echo   * Virtual environment  (%VENV_DIR%)
echo   * Desktop shortcuts    (DKI Engine, Uninstall DKI Engine)
echo   * Start Menu entries    (DKI Engine folder)
echo   * Local launch scripts  (%START_MENU%)
echo.
echo The following items are preserved:
echo   * %REPORT_DIR%\ (reports and configuration)
echo   * Python installation (system-wide)
echo.
set /p CONFIRM=Are you sure you want to continue? (y/N): 
if /I not "%CONFIRM%"=="Y" (
    echo.
    echo Uninstallation cancelled.
    pause
    exit /b 0
)

echo.
echo [1/5] Removing desktop shortcuts...
if exist "%DESKTOP%\DKI Engine.lnk" (
    del "%DESKTOP%\DKI Engine.lnk"
    echo   Removed desktop shortcut.
) else (
    echo   Desktop shortcut not found.
)
if exist "%DESKTOP%\Uninstall DKI Engine.lnk" (
    del "%DESKTOP%\Uninstall DKI Engine.lnk"
    echo   Removed uninstaller shortcut.
) else (
    echo   Uninstaller shortcut not found.
)

echo.
echo [2/5] Removing Start Menu entries...
if exist "%STARTMENU_DIR%" (
    rmdir /s /q "%STARTMENU_DIR%"
    echo   Removed Start Menu folder.
) else (
    echo   Start Menu folder not found.
)

echo.
echo [3/5] Removing virtual environment...
if exist "%VENV_DIR%" (
    rmdir /s /q "%VENV_DIR%"
    if exist "%VENV_DIR%" (
        echo   Warning: some files could not be removed. Please delete manually.
    ) else (
        echo   Virtual environment removed.
    )
) else (
    echo   Virtual environment not found.
)

echo.
echo [4/5] Removing installation artifacts...
set FILES_TO_REMOVE="%START_MENU%START_HERE.bat" "%START_MENU%DKI_ENGINE_LAUNCHER.bat" "%START_MENU%INSTALL_DKI_ENGINE.bat"
for %%F in (%FILES_TO_REMOVE%) do (
    if exist %%~F (
        del /f %%~F
        echo   Removed %%~F
    )
)
if exist "%START_MENU%UNINSTALL_DKI_ENGINE.bat" (
    rem Defer deleting this script until the end.
)
if exist "%INSTALL_FLAG%" del "%INSTALL_FLAG%"

echo.
echo [5/5] Cleanup complete.

echo.
echo DKI Engine has been removed from %BASE_DRIVE%.
echo.
echo To reinstall, run INSTALL_DKI_ENGINE.bat from %START_MENU%
echo or launch the main installer package again.

echo.
echo Press any key to close...
pause >nul

del /f "%~f0"
exit /b 0
