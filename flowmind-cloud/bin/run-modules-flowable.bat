@echo off
echo.
echo [信息] 使用 Jar 方式启动 Flowable 服务
echo.

cd %~dp0
cd ../ruoyi-modules/ruoyi-flowable/target

set JAVA_OPTS=-Xms512m -Xmx1024m -XX:MetaspaceSize=128m -XX:MaxMetaspaceSize=512m

java -Dfile.encoding=utf-8 %JAVA_OPTS% -jar ruoyi-modules-flowable.jar

cd ../../../bin
pause
