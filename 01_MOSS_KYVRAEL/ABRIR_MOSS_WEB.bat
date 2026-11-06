@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 api_server.py %*
) else (
  python api_server.py %*
)
exit /b %errorlevel%
