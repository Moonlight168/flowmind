@echo off
echo.
echo [信息] 使用Jar方式启动Gateway服务
echo.

cd %~dp0
cd ../ruoyi-gateway/target

set JAVA_OPTS=-Xms512m -Xmx1024m -XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=512m

java -Dfile.encoding=utf-8 %JAVA_OPTS% -jar ruoyi-gateway.jar

cd bin
pause
