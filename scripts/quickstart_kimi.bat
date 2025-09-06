@echo off
REM B1 React Engine - Kimi API 快速开始脚本

echo ========================================
echo B1 React Engine - Kimi API 快速开始
echo ========================================
echo.

REM 检查 Python 环境
python --version >nul 2>&1
if errorlevel 1 (
    echo 错误: 未找到 Python，请先安装 Python 3.8+
    pause
    exit /b 1
)

echo 当前 Python 版本:
python --version
echo.

REM 检查必要的包
echo 检查依赖包...
python -c "import openai" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 openai 包...
    pip install openai
)

python -c "import yaml" >nul 2>&1
if errorlevel 1 (
    echo 正在安装 pyyaml 包...
    pip install pyyaml
)

echo 依赖包检查完成
echo.

REM 设置环境变量提示
echo 请确保您已设置 Kimi API 密钥：
echo   set KIMI_API_KEY=your_kimi_api_key_here
echo   或者在 .env 文件中配置
echo.

REM 运行测试
echo 运行项目测试...
python test_project.py
if errorlevel 1 (
    echo 测试失败，请检查配置
    pause
    exit /b 1
)

echo.
echo 测试通过！现在可以使用以下命令：
echo.
echo 单任务执行:
echo   python main.py b1 --task "计算 2+3*4 的结果" --provider kimi
echo.
echo 批量任务执行:
echo   python main.py b2 --cases cases/cases.jsonl --policy policies/v1.yaml
echo.
echo 启动 Web 服务:
echo   python main.py server
echo.

pause
