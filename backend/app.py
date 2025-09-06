# -*- coding: utf-8 -*-
"""轻量后端：REST + SSE 实时观测（简化版）。"""
from __future__ import annotations
from fastapi import FastAPI
from fastapi.responses import JSONResponse, HTMLResponse, StreamingResponse
from fastapi.exceptions import HTTPException
from fastapi.staticfiles import StaticFiles
from fastapi.middleware.cors import CORSMiddleware
from typing import Dict
import json
import asyncio
import sys
import os
from schemas import RunIn, StepIn, FinalizeIn
import store

# 创建FastAPI应用
app = FastAPI()

# 添加CORS支持
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# 初始化数据库
store.init_db()

# 挂载静态文件目录 - 必须在路由定义之前
app.mount("/static", StaticFiles(directory="static"), name="static")

# Add the src directory to path for imports
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

# 导入分析模块（放在最后以避免循环导入）
try:
    from core.analysis import analyze_agent_quality
except ImportError:
    def analyze_agent_quality(data):
        return {"error": "Analysis module not available"}

_subscribers: Dict[str, asyncio.Queue] = {}


@app.post("/runs")
async def create_run(run: RunIn):
    store.insert_run(run.model_dump())
    _subscribers[run.run_id] = asyncio.Queue()
    return {"ok": True, "run_id": run.run_id}


@app.post("/runs/{run_id}/steps")
async def push_step(run_id: str, step: StepIn):
    store.insert_step(run_id, step.model_dump())
    if run_id in _subscribers:
        await _subscribers[run_id].put({"type": "step", **step.model_dump()})
    return {"ok": True}


@app.post("/runs/{run_id}/finalize")
async def finalize(run_id: str, fin: FinalizeIn):
    store.finalize_run(run_id, fin.final_answer or "", fin.metrics or {})
    if run_id in _subscribers:
        await _subscribers[run_id].put({"type": "final", "final_answer": fin.final_answer, "metrics": fin.metrics})
    return {"ok": True}


@app.get("/runs")
async def list_runs():
    return JSONResponse(store.list_runs())


@app.get("/runs/{run_id}")
async def get_run(run_id: str):
    return JSONResponse(store.get_run(run_id))


@app.get("/runs/{run_id}/analysis")
async def get_run_analysis(run_id: str):
    """获取运行的深度分析数据"""
    try:
        run_data = store.get_run(run_id)
        if not run_data:
            raise HTTPException(status_code=404, detail="Run not found")
        
        # 执行深度分析
        analysis_result = analyze_agent_quality(run_data)
        return JSONResponse(analysis_result)
    except Exception as e:
        # 如果分析失败，返回基础数据
        return JSONResponse({
            "error": str(e),
            "thinking_pattern": {"depth_score": 0, "coherence_score": 0, "efficiency_score": 0},
            "performance_metrics": {"total_tokens": 0, "avg_latency": 0, "success_rate": 0},
            "behavior_analysis": {"tool_usage_pattern": {}, "strategy_changes": []},
            "quality_assessment": {"overall": 0}
        })


@app.get("/runs/{run_id}/stream")
async def stream(run_id: str):
    async def event_gen():
        q = _subscribers.setdefault(run_id, asyncio.Queue())
        while True:
            item = await q.get()
            yield f"data: {json.dumps(item, ensure_ascii=False)}\n\n"
    return StreamingResponse(event_gen(), media_type="text/event-stream")


@app.get("/")
async def index():
    """主页重定向到静态文件"""
    with open("static/index.html", "r", encoding="utf-8") as f:
        return HTMLResponse(f.read())


@app.get("/debug")
async def debug():
    """调试信息"""
    import os
    return {
        "message": "服务器运行正常",
        "cwd": os.getcwd(),
        "static_exists": os.path.exists("static"),
        "index_exists": os.path.exists("static/index.html"),
        "static_files": os.listdir("static") if os.path.exists("static") else []
    }