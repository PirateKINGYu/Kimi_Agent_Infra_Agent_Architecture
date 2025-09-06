@echo off
REM 启动后端和运行任务的组合脚本

echo ===========================================
echo B1 React Engine - 后端观测演示
echo ===========================================
echo.

echo 1. 启动后端服务器...
start "B1 Backend Server" cmd /k "python main.py server"

echo 等待服务器启动...
timeout /t 3 /nobreak >nul

echo.
echo 2. 运行任务并发送到后端...
python main.py b1 --task "计算 23*19 加上 sqrt(144)" --policy policies/v1.yaml --sink http

echo.
echo 3. 任务完成！打开浏览器查看结果...
echo    访问地址: http://localhost:8000
echo.

pause
