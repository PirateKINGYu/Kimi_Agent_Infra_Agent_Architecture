# -*- coding: utf-8 -*-
from __future__ import annotations
from pydantic import BaseModel
from typing import Dict, Optional


class RunIn(BaseModel):
    run_id: str
    task: str
    model: str
    policy: str
    created_at: str


class StepIn(BaseModel):
    step_no: int
    thought: str
    action: Optional[str] = None
    action_input: Optional[str] = None
    observation: Optional[str] = None
    error: Optional[str] = None
    latency_s: float
    model_usage: Dict = {}


class FinalizeIn(BaseModel):
    final_answer: Optional[str] = None
    metrics: Dict = {}