@echo off
chcp 65001 >nul
REM 启动脚本 (Windows)

echo === ReAct Agent 启动脚本 ===

REM 检查 Python 版本
python --version
if %errorlevel% neq 0 (
    echo 错误: Python 未安装或不在 PATH 中
    pause
    exit /b 1
)

REM 检查依赖
echo 检查依赖包...
python -c "import langchain" 2>nul
if %errorlevel% neq 0 (
    echo 警告: LangChain 未安装，正在安装依赖...
    pip install -r requirements.txt
)

REM 检查环境配置
if not exist ".env" (
    echo 警告: .env 文件不存在，请配置 API 密钥
    pause
    exit /b 1
)

REM 选择运行模式
echo.
echo 请选择运行模式:
echo 1. 命令行演示模式
echo 2. 交互模式
echo 3. Web 界面
echo 4. 可视化分析

set /p choice=请输入选择 (1-4): 

if "%choice%"=="1" (
    echo 启动命令行演示模式...
    python main.py --mode demo
) else if "%choice%"=="2" (
    echo 启动交互模式...
    python main.py --mode interactive
) else if "%choice%"=="3" (
    echo 启动 Web 界面...
    streamlit run web_ui.py
) else if "%choice%"=="4" (
    echo 启动可视化分析...
    python main.py --mode viz
) else (
    echo 无效选择，启动演示模式...
    python main.py --mode demo
)

pause
