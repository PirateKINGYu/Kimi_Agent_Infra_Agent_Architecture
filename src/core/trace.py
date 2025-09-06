# -*- coding: utf-8 -*-
"""轨迹与指标数据模型。保持简洁，方便序列化与可视化。"""
from __future__ import annotations
from dataclasses import dataclass, field, asdict
from typing import Any, Dict, List, Optional
import json


@dataclass
class TraceStep:
    step: int
    thought: str  # 可脱敏
    action: Optional[str]
    action_input: Optional[str]
    observation: Optional[str]
    latency_s: float
    tool_latency_s: float = 0.0
    model_usage: Dict[str, Any] = field(default_factory=dict)
    error: Optional[str] = None


@dataclass
class RunTrace:
    task: str
    run_dir: str
    start_time: float
    run_id: str = ""
    model: str = ""
    policy: str = ""
    created_at: str = ""
    case_id: Optional[str] = None  # 批量评测映射
    steps: List[TraceStep] = field(default_factory=list)
    final_answer: Optional[str] = None
    metrics: Dict[str, Any] = field(default_factory=dict)
    end_time: Optional[float] = None

    def to_json(self) -> str:
        return json.dumps(asdict(self), ensure_ascii=False, indent=2)