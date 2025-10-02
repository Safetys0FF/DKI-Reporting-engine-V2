@echo off
setlocal
call "%~dp0DKI_ENGINE_LAUNCHER.bat"
set "EXIT_CODE=%ERRORLEVEL%"
endlocal
exit /b %EXIT_CODE%
