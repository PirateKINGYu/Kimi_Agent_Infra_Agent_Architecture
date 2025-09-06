@echo off
REM B1 快速启动脚本 (Windows 版本)
echo === B1 React Engine 快速启动 ===

echo 运行单任务: 计算并保存结果...
python main.py b1 --task "Compute (23*19)+sqrt(144) and save to calc.txt" --policy policies/v1.yaml

echo.
echo B1 任务完成！
echo 查看结果: runs/ 目录
pause
