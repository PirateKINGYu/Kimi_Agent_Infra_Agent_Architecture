# -*- coding: utf-8 -*-
"""简化的FastAPI应用测试静态文件"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse, JSONResponse
import uvicorn
import os

print(f"当前工作目录: {os.getcwd()}")
print(f"静态文件目录是否存在: {os.path.exists('static')}")
print(f"index.html是否存在: {os.path.exists('static/index.html')}")

app = FastAPI()

# 挂载静态文件目录
if os.path.exists("static"):
    app.mount("/static", StaticFiles(directory="static"), name="static")
    print("✅ 静态文件目录已挂载")
else:
    print("❌ 静态文件目录不存在")

@app.get("/")
async def root():
    return {"message": "服务器运行正常", "cwd": os.getcwd()}

@app.get("/debug")
async def debug():
    return {
        "cwd": os.getcwd(),
        "static_exists": os.path.exists("static"),
        "index_exists": os.path.exists("static/index.html"),
        "files": os.listdir("static") if os.path.exists("static") else []
    }

if __name__ == "__main__":
    print("启动简化服务器...")
    uvicorn.run(app, host="127.0.0.1", port=8000)
