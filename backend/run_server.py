#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""启动服务器脚本"""
import subprocess
import sys
import os

# 确保在正确的目录
os.chdir(r'C:\Users\33991\Desktop\kimi\backend')
print(f"当前目录: {os.getcwd()}")
print(f"静态文件目录存在: {os.path.exists('static')}")

# 启动服务器
try:
    print("启动FastAPI服务器...")
    result = subprocess.run([
        sys.executable, "-m", "uvicorn", 
        "app:app", 
        "--host", "127.0.0.1", 
        "--port", "8000", 
        "--reload"
    ], check=True)
except KeyboardInterrupt:
    print("服务器已停止")
except Exception as e:
    print(f"启动失败: {e}")
