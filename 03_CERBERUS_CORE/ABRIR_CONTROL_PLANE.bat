@echo off
cd /d "%~dp0"
echo C.E.R.B.E.R.U.S. Control Plane (leitura apenas)
echo Abre http://127.0.0.1:8890/ e usa o token apresentado abaixo.
py -3 control_plane.py
pause
