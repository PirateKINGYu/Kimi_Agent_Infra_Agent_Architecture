#!/bin/bash

# 启动脚本 (Linux/Mac)

echo "=== ReAct Agent 启动脚本 ==="

# 检查 Python 版本
python_version=$(python3 --version 2>&1)
echo "Python 版本: $python_version"

# 检查依赖
echo "检查依赖包..."
if ! python3 -c "import langchain" 2>/dev/null; then
    echo "警告: LangChain 未安装，正在安装依赖..."
    pip3 install -r requirements.txt
fi

# 检查环境配置
if [ ! -f ".env" ]; then
    echo "警告: .env 文件不存在，请配置 API 密钥"
    exit 1
fi

# 选择运行模式
echo ""
echo "请选择运行模式:"
echo "1. 命令行演示模式"
echo "2. 交互模式"
echo "3. Web 界面"
echo "4. 可视化分析"

read -p "请输入选择 (1-4): " choice

case $choice in
    1)
        echo "启动命令行演示模式..."
        python3 main.py --mode demo
        ;;
    2)
        echo "启动交互模式..."
        python3 main.py --mode interactive
        ;;
    3)
        echo "启动 Web 界面..."
        streamlit run web_ui.py
        ;;
    4)
        echo "启动可视化分析..."
        python3 main.py --mode viz
        ;;
    *)
        echo "无效选择，启动演示模式..."
        python3 main.py --mode demo
        ;;
esac
