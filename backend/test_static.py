# -*- coding: utf-8 -*-
"""测试静态文件路由"""
from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles
from fastapi.responses import HTMLResponse
import uvicorn

app = FastAPI()

# 挂载静态文件目录
app.mount("/static", StaticFiles(directory="static"), name="static")

@app.get("/")
async def root():
    return {"message": "服务器运行正常"}

@app.get("/test")
async def test():
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())

if __name__ == "__main__":
    print("启动测试服务器...")
    print("访问 http://localhost:8000/static/index.html 测试静态文件")
    print("访问 http://localhost:8000/test 测试HTML响应")
    uvicorn.run(app, host="0.0.0.0", port=8000)
