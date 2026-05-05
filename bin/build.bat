@echo off
set "SCRIPT_DIR=%~dp0"

echo.
echo ============================================
echo FlowMind Build Script
echo ============================================
echo.

echo [Step 1/3] Building Java project...
cd /d "%SCRIPT_DIR%..\flowmind-cloud"
call mvn clean package -DskipTests
if errorlevel 1 (
    echo [ERROR] Java build failed
    cd /d "%SCRIPT_DIR%"
    exit /b 1
)
echo   - Java build successful

echo [Step 2/3] Copying JAR files to Docker directory...
set "DOCKER_DIR=..\docker\cloud\ruoyi"

copy /Y ruoyi-gateway\target\ruoyi-gateway.jar "%DOCKER_DIR%\gateway\jar\" >nul
echo   - gateway

copy /Y ruoyi-auth\target\ruoyi-auth.jar "%DOCKER_DIR%\auth\jar\" >nul
echo   - auth

copy /Y ruoyi-modules\ruoyi-system\target\ruoyi-modules-system.jar "%DOCKER_DIR%\modules\system\jar\" >nul
echo   - system

copy /Y ruoyi-modules\ruoyi-flowable\target\ruoyi-modules-flowable.jar "%DOCKER_DIR%\modules\flowable\jar\" >nul
echo   - flowable

copy /Y ruoyi-modules\ruoyi-file\target\ruoyi-modules-file.jar "%DOCKER_DIR%\modules\file\jar\" >nul
echo   - file

copy /Y ruoyi-modules\ruoyi-gen\target\ruoyi-modules-gen.jar "%DOCKER_DIR%\modules\gen\jar\" >nul
echo   - gen

copy /Y ruoyi-modules\ruoyi-job\target\ruoyi-modules-job.jar "%DOCKER_DIR%\modules\job\jar\" >nul
echo   - job

copy /Y ruoyi-visual\ruoyi-monitor\target\ruoyi-visual-monitor.jar "%DOCKER_DIR%\visual\monitor\jar\" >nul
echo   - visual

echo [Step 3/3] Building Frontend...
cd /d "%SCRIPT_DIR%..\flowmind-ui"
call yarn build:prod
if errorlevel 1 (
    echo [ERROR] Frontend build failed
    cd /d "%SCRIPT_DIR%"
    exit /b 1
)

echo   - Copying frontend dist to nginx...
xcopy /E /Y /I dist\* ..\docker\cloud\nginx\html\dist\ >nul
echo   - Frontend build successful

cd /d "%SCRIPT_DIR%"

echo.
echo ============================================
echo Build completed!
echo ============================================
echo.
echo Next: cd docker\flowmind ^&^& docker-compose -f docker-compose.prod.yml up -d --build
echo.
