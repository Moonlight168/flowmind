@echo off
set "SCRIPT_DIR=%~dp0"

echo.
echo ============================================
echo FlowMind Stop Script (SAFE MODE)
echo ============================================
echo.

echo [1/2] Stopping FlowMind processes...

powershell -NoProfile -Command "Get-Process | Where-Object {$_.MainWindowTitle -like '*FlowMind-*'} | ForEach-Object { Stop-Process -Id $_.Id -Force }"

echo [OK] FlowMind processes stopped
echo.

set "DOCKER_DIR=%SCRIPT_DIR%..\docker\cloud"

echo [2/2] Stopping Docker containers...
cd /d "%DOCKER_DIR%"
docker compose stop

echo [OK] Docker stopped
echo.

echo ============================================
echo All FlowMind services stopped safely
echo ============================================
echo.

cd /d "%SCRIPT_DIR%"
exit /b 0