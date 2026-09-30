@echo off
setlocal

set "SCRIPT_DIR=%~dp0"
set "DOCKER_DIR=%SCRIPT_DIR%..\docker\flowmind"

echo.
echo ============================================
echo FlowMind Docker Development Environment
echo ============================================
echo.

cd /d "%DOCKER_DIR%"
docker compose up -d --remove-orphans --wait --wait-timeout 300
if errorlevel 1 (
    echo [ERROR] Docker development environment failed to start
    exit /b 1
)

echo.
echo [OK] FlowMind development environment started
echo   Frontend: http://localhost:18088
echo   Monitor:  http://localhost:18090
echo   Nacos:    http://localhost:19090/nacos
echo.
echo Vue and AI source changes reload automatically.
echo Java changes still require rebuilding and restarting the affected service.
echo File, Gen, Job, Monitor, Langfuse and Sentinel remain optional and are not started.

exit /b 0
