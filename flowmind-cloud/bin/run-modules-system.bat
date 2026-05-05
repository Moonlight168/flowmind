@echo off
echo.
echo [信息] 使用Jar方式启动Modules-System服务
echo.

cd %~dp0
cd ../ruoyi-modules/ruoyi-system/target

set JAVA_OPTS=-Xms512m -Xmx1024m -XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=512m

java -Dfile.encoding=utf-8 %JAVA_OPTS% -jar ruoyi-modules-system.jar

cd bin
pause
