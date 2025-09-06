# -*- coding: utf-8 -*-
"""
ReAct Engine 核心：支持步骤轨迹、工具调用、指标统计
"""

import os
import json
import time
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass
from .trace import TraceStep, RunTrace
from .toolbus import ToolBus
from .model_adapter import ModelAdapter

SYSTEM_PROMPT = """You are a helpful AI assistant. You can use tools to help solve problems.

Available tools: [TOOL_NAMES]

Always follow this format:
Thought: [your reasoning]
Action: [tool name or 'Final Answer']
Action Input: [tool input or your final response]

When you have enough information to answer, use:
Action: Final Answer
Action Input: [your complete answer]
"""

@dataclass
class ReactConfig:
    """ReAct 配置"""
    max_steps: int = 10
    redact_secrets: bool = True
    allow_empty_action_input: bool = True

class ReactEngine:
    """ReAct 引擎核心实现"""
    
    def __init__(self, model: ModelAdapter, tools: ToolBus, config: Optional[ReactConfig] = None, sink=None):
        self.model = model
        self.tools = tools
        self.config = config or ReactConfig()
        self.max_steps = self.config.max_steps
        self.sink = sink
    
    def run(self, task: str, run_dir: str = "runs/default") -> RunTrace:
        """执行任务，返回完整轨迹"""
        start_time = time.time()
        run = RunTrace(task=task, run_dir=run_dir, start_time=start_time)
        
        # 如果有 sink，通知开始
        if self.sink:
            import uuid
            run_id = str(uuid.uuid4())[:8]
            run.run_id = run_id
            run.model = self.model.name()
            run.policy = "default"
            run.created_at = time.strftime("%Y-%m-%d %H:%M:%S")
            self.sink.run_start(run)
        
        # 创建运行目录
        os.makedirs(run_dir, exist_ok=True)
        try:
            self.tools.set_workdir(run_dir)  # 若是 LocalBus 则生效
        except Exception:
            pass
        
        # 构造系统提示
        system = SYSTEM_PROMPT.replace("[TOOL_NAMES]", ", ".join(self.tools.list_tools().keys()))
        steps: List[TraceStep] = []
        
        for i in range(1, self.max_steps + 1):
            # 拼装最近上下文（简单：附加最近若干步）
            ctx_blocks = []
            for s in steps[-3:]:  # 减少上下文长度，降低 token 使用
                ctx_blocks.append(
                    f"Step {s.step} -> Thought: {s.thought}\nAction: {s.action}\nAction Input: {s.action_input}\nObservation: {s.observation}"
                )
            user = (
                f"Task: {task}\n\nAvailable Tools: {', '.join(self.tools.list_tools().keys())}\n\n"
                f"Recent Steps:\n" + ("\n\n".join(ctx_blocks) if ctx_blocks else "<none>") +
                "\n\nIMPORTANT:\n- 若已足够信息，请输出 Final Answer。"
            )
            
            messages = [{"role": "system", "content": system}, {"role": "user", "content": user}]
            
            # 添加延迟以避免速率限制
            if i > 1:  # 第一步不延迟
                time.sleep(1)  # 每步之间等待 1 秒
            
            text, meta = self.model.chat(messages)
            
            final, action, ainput, thought = self._parse(text)
            if final is not None:
                step = TraceStep(step=i, thought=self._redact(thought), action=None, action_input=None,
                               observation=None, latency_s=meta.get("latency_s", 0.0), model_usage=meta.get("usage", {}))
                steps.append(step)
                run.final_answer = final
                
                # 发送最终步骤到 sink
                if self.sink:
                    self.sink.emit_step(run.run_id, step)
                    self.sink.run_end(run)
                break
            
            obs, err = None, None
            tool_lat = 0.0
            if action and action.lower() != 'none':
                res = self.tools.call(action, ainput or "")
                obs = res.get("output")
                err = res.get("error")
                tool_lat = float(res.get("latency_s", 0.0))
            
            step = TraceStep(step=i, thought=self._redact(thought), action=action, action_input=ainput,
                           observation=obs or err or "No output", latency_s=meta.get("latency_s", 0.0),
                           tool_latency_s=tool_lat, model_usage=meta.get("usage", {}))
            steps.append(step)
            
            # 发送步骤到 sink
            if self.sink:
                self.sink.emit_step(run.run_id, step)
        
        run.steps = steps
        run.end_time = time.time()
        return run
    
    def _parse(self, text: str) -> Tuple[Optional[str], Optional[str], Optional[str], str]:
        """解析模型输出"""
        lines = text.strip().split('\n')
        thought, action, action_input, final_answer = "", None, None, None
        
        for line in lines:
            line = line.strip()
            if line.startswith('Thought:'):
                thought = line[8:].strip()
            elif line.startswith('Action:'):
                action = line[7:].strip()
                if action.lower() == 'final answer':
                    action = 'Final Answer'
            elif line.startswith('Action Input:'):
                action_input = line[13:].strip()
                if action == 'Final Answer':
                    final_answer = action_input
        
        return final_answer, action, action_input, thought
    
    def _redact(self, text: str) -> str:
        """脱敏处理"""
        if not self.config.redact_secrets:
            return text
        # 简单的密钥脱敏
        import re
        text = re.sub(r'sk-[a-zA-Z0-9]{32,}', 'sk-***', text)
        text = re.sub(r'Bearer [a-zA-Z0-9]{32,}', 'Bearer ***', text)
        return text