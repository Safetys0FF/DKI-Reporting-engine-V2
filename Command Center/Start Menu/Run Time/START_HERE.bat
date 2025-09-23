@echo off
setlocal
call "F:\DKI-Report-Engine\Report Engine\Start Menu\DKI_ENGINE_LAUNCHER.bat"
set "EXIT_CODE=%ERRORLEVEL%"
endlocal
exit /b %EXIT_CODE%
