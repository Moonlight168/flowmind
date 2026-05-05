@echo off
echo.
echo [信息] 清空项目target目录文件
echo.

%~d0
cd %~dp0

cd ..
call mvn clean

pause
