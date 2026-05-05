@echo off
setlocal enabledelayedexpansion
:: FlowMind unified startup script

set "SCRIPT_DIR=%~dp0"
set "DOCKER_DIR=%SCRIPT_DIR%..\docker\cloud"
set "BACKEND_DIR=%SCRIPT_DIR%..\flowmind-cloud"
set "FRONTEND_DIR=%SCRIPT_DIR%..\flowmind-ui"

echo.
echo ============================================
echo FlowMind Unified Startup
echo ============================================
echo.

:: Check Docker containers
docker ps --format "{{.Names}}" | findstr /i "flowmind-nacos flowmind-mysql flowmind-redis" >nul 2>&1
if !errorlevel! equ 0 (
    set "DOCKER_RUNNING=1"
    echo [INFO] Docker containers already running
) else (
    set "DOCKER_RUNNING=0"
)

:: Check port 9001 (backend)
netstat -ano | findstr ":9001 " | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    set "BACKEND_SKIP=1"
    echo [INFO] Backend Gateway already running
) else (
    set "BACKEND_SKIP=0"
)

:: Check port 88 (frontend)
netstat -ano | findstr ":88 " | findstr "LISTENING" >nul 2>&1
if !errorlevel! equ 0 (
    set "FRONTEND_SKIP=1"
    echo [INFO] Frontend already running
) else (
    set "FRONTEND_SKIP=0"
)
echo.

:: Step 1: Start Docker containers
if "!DOCKER_RUNNING!"=="0" (
    echo [Step 1/3] Starting Docker containers...
    cd /d "%DOCKER_DIR%"
    docker compose up -d
    :: docker compose up -d may return non-zero even when containers start successfully
    :: Check actual container status instead of relying on exit code
    timeout /t 15 /nobreak >nul

    docker ps --format "{{.Names}}" | findstr /i "flowmind-nacos flowmind-mysql flowmind-redis" >nul 2>&1
    if !errorlevel! neq 0 (
        echo [ERROR] Docker containers failed to start
        exit /b 1
    )
    echo [OK] Docker containers started
) else (
    echo [SKIP] Docker containers already running
)
echo.

:: Step 2: Start Java backend
if "!BACKEND_SKIP!"=="0" (
    echo [Step 2/3] Starting Java backend...
    start "FlowMind-Backend" /min "%BACKEND_DIR%\bin\run-all.bat"

    set "BACKEND_TIMEOUT=180"
    set "ELAPSED=0"

    :wait_backend
    timeout /t 2 /nobreak >nul
    set /a ELAPSED+=2

    netstat -ano | findstr ":9001 " | findstr "LISTENING" >nul 2>&1
    if !errorlevel! equ 0 goto backend_ready
    netstat -ano | findstr ":9002 " | findstr "LISTENING" >nul 2>&1
    if !errorlevel! equ 0 goto backend_ready

    if !ELAPSED! geq !BACKEND_TIMEOUT! (
        echo [ERROR] Backend startup timeout
        exit /b 1
    )
    goto wait_backend

    :backend_ready
    echo [OK] Java backend started
) else (
    echo [SKIP] Backend already running
)
echo.

:: Step 3: Start Frontend
if "!FRONTEND_SKIP!"=="0" (
    echo [Step 3/3] Starting Frontend...
    start "FlowMind-Frontend" cmd /min /c "cd /d "%FRONTEND_DIR%" && npm run dev & timeout /t 2 /nobreak >nul & title FlowMind-Frontend"
    timeout /t 10 /nobreak >nul
    echo [OK] Frontend started
) else (
    echo [SKIP] Frontend already running
)
echo.

echo ============================================
echo FlowMind startup complete!
echo ============================================
echo.
echo Services:
echo   - Docker:  http://localhost:19090 (Nacos)
echo   - Gateway: http://localhost:9001
echo   - Frontend: http://localhost:88
echo.

exit /b 0
