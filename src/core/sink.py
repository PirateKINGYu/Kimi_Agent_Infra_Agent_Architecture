# -*- coding: utf-8 -*-
"""观测数据出口：FileSink（默认）与 HttpSink（推送到后端）。"""
from __future__ import annotations
import os
import json
from typing import Optional
from .trace import RunTrace, TraceStep
from .visualize import render_html


class TraceSink:
    def run_start(self, run: RunTrace):
        raise NotImplementedError
    
    def emit_step(self, run_id: str, step: TraceStep):
        raise NotImplementedError
    
    def run_end(self, run: RunTrace):
        raise NotImplementedError


class FileSink(TraceSink):
    def __init__(self, base_dir: str = "runs"):
        self.base = base_dir
    
    def _dir(self, run_id: str) -> str:
        p = os.path.join(self.base, run_id)
        os.makedirs(p, exist_ok=True)
        return p
    
    def get_dir(self, run_id: str) -> str:
        """提供给引擎获取当前 run 的落盘目录。"""
        return self._dir(run_id)
    
    def run_start(self, run: RunTrace):
        self._dir(run.run_id)
    
    def emit_step(self, run_id: str, step: TraceStep):
        # 简化：不做逐步追加；结束时写全量即可
        pass
    
    def run_end(self, run: RunTrace):
        d = self._dir(run.run_id)
        with open(os.path.join(d, "trace.json"), "w", encoding="utf-8") as f:
            f.write(run.to_json())
        with open(os.path.join(d, "report.html"), "w", encoding="utf-8") as f:
            f.write(render_html(run))


class HttpSink(TraceSink):
    """将轨迹推送到后端服务（可选）。"""
    def __init__(self, base_url: str):
        self.base_url = base_url.rstrip("/")
        try:
            import requests  # 仅在使用时依赖
        except Exception:
            raise RuntimeError("HttpSink 需要 requests 库")
        self._requests = requests
        self._run_id_remote: Optional[str] = None

    def run_start(self, run: RunTrace):
        r = self._requests.post(f"{self.base_url}/runs", json={
            "run_id": run.run_id, "task": run.task, "model": run.model, "policy": run.policy, "created_at": run.created_at
        }, timeout=10)
        r.raise_for_status()
        self._run_id_remote = run.run_id

    def emit_step(self, run_id: str, step: TraceStep):
        r = self._requests.post(f"{self.base_url}/runs/{run_id}/steps", json={
            "step_no": step.step, "thought": step.thought, "action": step.action,
            "action_input": step.action_input, "observation": step.observation,
            "error": step.error, "latency_s": step.latency_s, "model_usage": step.model_usage
        }, timeout=10)
        r.raise_for_status()

    def run_end(self, run: RunTrace):
        r = self._requests.post(f"{self.base_url}/runs/{run.run_id}/finalize", json={
            "final_answer": run.final_answer, "metrics": run.metrics
        }, timeout=10)
        r.raise_for_status()