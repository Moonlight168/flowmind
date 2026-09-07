@echo off
set "SCRIPT_DIR=%~dp0"

echo.
echo ============================================
echo FlowMind Stop Script (SAFE MODE)
echo ============================================
echo.

echo [1/3] Stopping AI service (port 8000)...
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /C:":8000 " ^| findstr "LISTENING"') do taskkill /PID %%p /T /F >nul 2>&1
echo [OK] AI service stopped
echo.

echo [2/3] Stopping FlowMind processes...
powershell -NoProfile -Command "Get-Process | Where-Object {$_.MainWindowTitle -like '*FlowMind-*'} | ForEach-Object { Stop-Process -Id $_.Id -Force }"

:: Port-based fallbacks in case window-title matching missed a process tree
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /C:":88 " ^| findstr "LISTENING"') do taskkill /PID %%p /T /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /C:":9001 " ^| findstr "LISTENING"') do taskkill /PID %%p /T /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /C:":9002 " ^| findstr "LISTENING"') do taskkill /PID %%p /T /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /C:":9003 " ^| findstr "LISTENING"') do taskkill /PID %%p /T /F >nul 2>&1
for /f "tokens=5" %%p in ('netstat -ano ^| findstr /C:":9007 " ^| findstr "LISTENING"') do taskkill /PID %%p /T /F >nul 2>&1
echo [OK] FlowMind processes stopped
echo.

set "DOCKER_DIR=%SCRIPT_DIR%..\docker\cloud"

echo [3/3] Stopping Docker containers...
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
