@echo off
title garciabermeo.net
cd /d "%~dp0"

echo.
echo  garciabermeo.net - Gestion de expedientes judiciales
echo  Iniciando aplicacion...
echo.

start "" cmd /c "timeout /t 5 /nobreak >nul && start http://localhost:8501"

powershell -NoExit -ExecutionPolicy Bypass -File "%~dp0run_app.ps1"
