@echo off
setlocal enabledelayedexpansion
:: FlowMind unified startup script

set "SCRIPT_DIR=%~dp0"
set "DOCKER_DIR=%SCRIPT_DIR%..\docker\cloud"
set "BACKEND_DIR=%SCRIPT_DIR%..\flowmind-cloud"
set "FRONTEND_DIR=%SCRIPT_DIR%..\flowmind-ui"
set "AI_DIR=%SCRIPT_DIR%..\flowmind-ai-flow\ai-service"
set "VENV_PY=%SCRIPT_DIR%..\.venv\Scripts\python.exe"

echo.
echo ============================================
echo FlowMind Unified Startup
echo ============================================
echo.

:: ---------- Service state checks ----------
set "DOCKER_RUNNING=0"
docker ps --format "{{.Names}}" | findstr /i "flowmind-nacos flowmind-mysql flowmind-redis" >nul 2>&1
if not errorlevel 1 set "DOCKER_RUNNING=1"

set "BACKEND_SKIP=0"
netstat -ano | findstr /C:":9001 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 set "BACKEND_SKIP=1"

set "AI_SKIP=0"
netstat -ano | findstr /C:":8000 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 set "AI_SKIP=1"

set "FRONTEND_SKIP=0"
netstat -ano | findstr /C:":88 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 set "FRONTEND_SKIP=1"

if "%DOCKER_RUNNING%"=="1" echo [INFO] Docker containers already running
if "%BACKEND_SKIP%"=="1" echo [INFO] Backend Gateway already running
if "%AI_SKIP%"=="1" echo [INFO] AI service already running
if "%FRONTEND_SKIP%"=="1" echo [INFO] Frontend already running
echo.

:: ---------- Step 1: Docker containers ----------
if "%DOCKER_RUNNING%"=="1" goto docker_done

echo [Step 1/4] Starting Docker containers...
cd /d "%DOCKER_DIR%"
docker compose up -d
:: docker compose up -d may return non-zero even when containers start successfully;
:: verify actual container status instead.
ping -n 16 127.0.0.1 >nul

docker ps --format "{{.Names}}" | findstr /i "flowmind-nacos flowmind-mysql flowmind-redis" >nul 2>&1
if not errorlevel 1 (
    echo [OK] Docker containers started
    goto docker_done
)
echo [ERROR] Docker containers failed to start
exit /b 1

:docker_done
if "%DOCKER_RUNNING%"=="1" echo [SKIP] Docker containers already running
echo.

:: ---------- Step 2: AI service (FastAPI + LangGraph, port 8000) ----------
if "%AI_SKIP%"=="1" goto ai_skip
if not exist "%VENV_PY%" (
    echo [WARN] Python venv not found: %VENV_PY%
    echo        AI service skipped. Manual: cd docker/ai-service ^&^& docker-compose up -d
    goto ai_skip
)

echo [Step 2/4] Starting AI service...
:: cmd always exports a stray PROMPT var ($P$G); pydantic-settings would parse it as the
:: nested "prompt" config field and crash. Strip it so the child process inherits clean env.
set "PROMPT="
start "FlowMind-AI" /min /D "%AI_DIR%" "%VENV_PY%" -m uvicorn app.main:app --host 0.0.0.0 --port 8000

set /a ELAPSED=0
:wait_ai
ping -n 3 127.0.0.1 >nul
set /a ELAPSED+=2
netstat -ano | findstr /C:":8000 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 goto ai_ready
if !ELAPSED! lss 180 goto wait_ai
echo [ERROR] AI service startup timeout (port 8000 not listening). Check .venv deps and Nacos.
exit /b 1

:ai_ready
echo [OK] AI service started
goto ai_done
:ai_skip
echo [SKIP] AI service already running
:ai_done
echo.

:: ---------- Step 3: Java backend ----------
if "%BACKEND_SKIP%"=="1" goto backend_skip

echo [Step 3/4] Starting Java backend...
start "FlowMind-Backend" /min "%BACKEND_DIR%\bin\run-all.bat"

set /a ELAPSED=0
:wait_backend
ping -n 3 127.0.0.1 >nul
set /a ELAPSED+=2
netstat -ano | findstr /C:":9001 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 goto backend_ready
netstat -ano | findstr /C:":9002 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 goto backend_ready
if !ELAPSED! lss 180 goto wait_backend
echo [ERROR] Backend startup timeout
exit /b 1

:backend_ready
echo [OK] Java backend started
goto backend_done
:backend_skip
echo [SKIP] Backend already running
:backend_done
echo.

:: ---------- Step 4: Frontend (vite dev, port 88) ----------
if "%FRONTEND_SKIP%"=="1" goto frontend_skip

echo [Step 4/4] Starting Frontend...
start "FlowMind-Frontend" /min /D "%FRONTEND_DIR%" cmd /c "yarn dev"

set /a ELAPSED=0
:wait_frontend
ping -n 3 127.0.0.1 >nul
set /a ELAPSED+=2
netstat -ano | findstr /C:":88 " | findstr "LISTENING" >nul 2>&1
if not errorlevel 1 goto frontend_ready
if !ELAPSED! lss 90 goto wait_frontend
echo [ERROR] Frontend startup timeout. Open a terminal in flowmind-ui to see vite errors.
exit /b 1

:frontend_ready
echo [OK] Frontend started
goto frontend_done
:frontend_skip
echo [SKIP] Frontend already running
:frontend_done
echo.

echo ============================================
echo FlowMind startup complete!
echo ============================================
echo.
echo Services:
echo   - Docker:   http://localhost:19090 (Nacos)
echo   - AI:       http://localhost:8000 (docs: /docs)
echo   - Gateway:  http://localhost:9001
echo   - Frontend: http://localhost:88
echo.

exit /b 0
