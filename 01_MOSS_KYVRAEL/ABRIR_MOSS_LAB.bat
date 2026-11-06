@echo off
setlocal
cd /d "%~dp0"
where py >nul 2>nul
if %errorlevel%==0 (
  py -3 cli.py %*
) else (
  python cli.py %*
)
exit /b %errorlevel%
