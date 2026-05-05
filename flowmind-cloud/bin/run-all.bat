@echo off
:: Set JAVA_HOME if not defined - use setx to persist for future sessions
if not defined JAVA_HOME setx JAVA_HOME "F:\jdk\jdk17" >nul 2>&1
set "JAVA_HOME=F:\jdk\jdk17"

:: FlowMind Java Microservices Startup Script
:: Function: Build all modules then start services in order: Gateway -> Auth -> System -> Flowable

echo.
echo ============================================
echo FlowMind Java Services Launcher
echo ============================================
echo.
echo Startup order:
echo   0. Build all modules
echo   1. Gateway (port 9001)
echo   2. Auth (port 9002)
echo   3. System (port 9003)
echo   4. Flowable (port 9007)
echo.

set "JAVA_OPTS=-Xms512m -Xmx1024m -XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=512m"
set "BASE_DIR=%~dp0.."
set "STARTUP_TIMEOUT=120"

:: Step 0: Build all modules first
echo [Step 0/5] Building all modules...
cd /d "%BASE_DIR%"
call mvn clean install -DskipTests
if %errorlevel% neq 0 (
    echo [ERROR] Build failed
    exit /b 1
)
echo [OK] Build completed
echo.

:: Start Gateway
echo [Step 1/5] Starting Gateway service...
start /min "FlowMind-Gateway" cmd /D /k "set "JAVA_HOME=%JAVA_HOME%" && cd /d "%BASE_DIR%\ruoyi-gateway" && mvn spring-boot:run -Dspring-boot.run.jvmArguments="-DJAVA_HOME=%JAVA_HOME% %JAVA_OPTS% -Dorg.apache.catalina.startup.EXIT_ON_INIT_FAILURE=true -Dserver.tomcat.basedir=./target/tomcat -Dspring.profiles.active=dev"
call :wait_for_port 9001 Gateway
if %errorlevel% neq 0 exit /b 1

:: Start Auth
echo [Step 2/5] Starting Auth service...
start /min "FlowMind-Auth" cmd /D /k "set "JAVA_HOME=%JAVA_HOME%" && cd /d "%BASE_DIR%\ruoyi-auth" && mvn spring-boot:run -Dspring-boot.run.jvmArguments="-DJAVA_HOME=%JAVA_HOME% %JAVA_OPTS% -Dorg.apache.catalina.startup.EXIT_ON_INIT_FAILURE=true -Dserver.tomcat.basedir=./target/tomcat -Dspring.profiles.active=dev"
call :wait_for_port 9002 Auth
if %errorlevel% neq 0 exit /b 1

:: Start System
echo [Step 3/5] Starting System service...
start /min "FlowMind-System" cmd /D /k "set "JAVA_HOME=%JAVA_HOME%" && cd /d "%BASE_DIR%\ruoyi-modules\ruoyi-system" && mvn spring-boot:run -Dspring-boot.run.jvmArguments="-DJAVA_HOME=%JAVA_HOME% %JAVA_OPTS% -Dorg.apache.catalina.startup.EXIT_ON_INIT_FAILURE=true -Dserver.tomcat.basedir=./target/tomcat -Dspring.profiles.active=dev"
call :wait_for_port 9003 System
if %errorlevel% neq 0 exit /b 1

:: Start Flowable
echo [Step 4/5] Starting Flowable service...
start /min "FlowMind-Flowable" cmd /D /k "set "JAVA_HOME=%JAVA_HOME%" && cd /d "%BASE_DIR%\ruoyi-modules\ruoyi-flowable" && mvn spring-boot:run -Dspring-boot.run.jvmArguments="-DJAVA_HOME=%JAVA_HOME% %JAVA_OPTS% -Dorg.apache.catalina.startup.EXIT_ON_INIT_FAILURE=true -Dserver.tomcat.basedir=./target/tomcat -Dspring.profiles.active=dev"
call :wait_for_port 9007 Flowable
if %errorlevel% neq 0 exit /b 1

echo.
echo ============================================
echo [DONE] All services started successfully!
echo ============================================
echo.
exit /b 0

:: Port check function
:wait_for_port
set "PORT=%~1"
set "SERVICE=%~2"
set "ELAPSED=0"

echo Waiting for %SERVICE% on port %PORT%...

:check_loop
timeout /t 1 /nobreak >nul 2>&1
set /a ELAPSED+=1

netstat -an | findstr "LISTENING" | findstr ":%PORT%" >nul 2>&1
if %errorlevel% equ 0 (
    echo   %SERVICE% is ready on port %PORT%
    echo.
    exit /b 0
)

if %ELAPSED% geq %STARTUP_TIMEOUT% (
    echo   ERROR: %SERVICE% failed to start on port %PORT%
    exit /b 1
)

goto :check_loop
