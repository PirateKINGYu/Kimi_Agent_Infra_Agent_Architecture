"""
轨迹捕获和可观测性模块
记录 Agent 执行过程中的所有关键信息
"""
import json
import time
import uuid
from typing import Dict, Any, List, Optional
from datetime import datetime
from dataclasses import dataclass, asdict
from enum import Enum


class StepType(Enum):
    """步骤类型枚举"""
    THOUGHT = "thought"      # 思考
    ACTION = "action"        # 行动
    OBSERVATION = "observation"  # 观察
    FINAL_ANSWER = "final_answer"  # 最终答案


@dataclass
class ExecutionStep:
    """执行步骤记录"""
    step_id: str
    step_type: StepType
    content: str
    timestamp: str
    execution_time: float = 0.0
    token_count: int = 0
    metadata: Dict[str, Any] = None
    
    def __post_init__(self):
        if self.metadata is None:
            self.metadata = {}


@dataclass
class ToolCall:
    """工具调用记录"""
    tool_name: str
    input_params: Dict[str, Any]
    output: Dict[str, Any]
    execution_time: float
    success: bool
    timestamp: str


@dataclass
class ExecutionTrace:
    """完整的执行轨迹"""
    trace_id: str
    query: str
    start_time: str
    end_time: Optional[str] = None
    steps: List[ExecutionStep] = None
    tool_calls: List[ToolCall] = None
    total_tokens: int = 0
    total_api_calls: int = 0
    success: bool = True
    final_answer: str = ""
    error_message: str = ""
    
    def __post_init__(self):
        if self.steps is None:
            self.steps = []
        if self.tool_calls is None:
            self.tool_calls = []


class TraceCapture:
    """轨迹捕获器"""
    
    def __init__(self):
        self.current_trace: Optional[ExecutionTrace] = None
        self.traces: List[ExecutionTrace] = []
    
    def start_trace(self, query: str) -> str:
        """开始新的轨迹记录"""
        trace_id = str(uuid.uuid4())
        self.current_trace = ExecutionTrace(
            trace_id=trace_id,
            query=query,
            start_time=datetime.now().isoformat()
        )
        return trace_id
    
    def add_step(self, step_type: StepType, content: str, 
                 execution_time: float = 0.0, token_count: int = 0,
                 metadata: Dict[str, Any] = None) -> str:
        """添加执行步骤"""
        if not self.current_trace:
            raise ValueError("没有活动的轨迹记录")
        
        step_id = str(uuid.uuid4())
        step = ExecutionStep(
            step_id=step_id,
            step_type=step_type,
            content=content,
            timestamp=datetime.now().isoformat(),
            execution_time=execution_time,
            token_count=token_count,
            metadata=metadata or {}
        )
        
        self.current_trace.steps.append(step)
        self.current_trace.total_tokens += token_count
        
        return step_id
    
    def add_tool_call(self, tool_name: str, input_params: Dict[str, Any],
                      output: Dict[str, Any], execution_time: float,
                      success: bool):
        """记录工具调用"""
        if not self.current_trace:
            return
        
        tool_call = ToolCall(
            tool_name=tool_name,
            input_params=input_params,
            output=output,
            execution_time=execution_time,
            success=success,
            timestamp=datetime.now().isoformat()
        )
        
        self.current_trace.tool_calls.append(tool_call)
        self.current_trace.total_api_calls += 1
    
    def end_trace(self, success: bool = True, final_answer: str = "",
                  error_message: str = ""):
        """结束轨迹记录"""
        if not self.current_trace:
            return
        
        self.current_trace.end_time = datetime.now().isoformat()
        self.current_trace.success = success
        self.current_trace.final_answer = final_answer
        self.current_trace.error_message = error_message
        
        self.traces.append(self.current_trace)
        self.current_trace = None
    
    def get_trace(self, trace_id: str) -> Optional[ExecutionTrace]:
        """获取指定的轨迹"""
        for trace in self.traces:
            if trace.trace_id == trace_id:
                return trace
        return None
    
    def get_all_traces(self) -> List[ExecutionTrace]:
        """获取所有轨迹"""
        return self.traces.copy()
    
    def export_trace(self, trace_id: str, format: str = "json") -> str:
        """导出轨迹数据"""
        trace = self.get_trace(trace_id)
        if not trace:
            raise ValueError(f"轨迹不存在: {trace_id}")
        
        if format == "json":
            return json.dumps(asdict(trace), ensure_ascii=False, indent=2)
        else:
            raise ValueError(f"不支持的格式: {format}")
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        if not self.traces:
            return {"total_traces": 0}
        
        total_traces = len(self.traces)
        successful_traces = sum(1 for t in self.traces if t.success)
        total_tokens = sum(t.total_tokens for t in self.traces)
        total_api_calls = sum(t.total_api_calls for t in self.traces)
        
        avg_execution_time = 0
        if self.traces:
            execution_times = []
            for trace in self.traces:
                if trace.start_time and trace.end_time:
                    start = datetime.fromisoformat(trace.start_time)
                    end = datetime.fromisoformat(trace.end_time)
                    execution_times.append((end - start).total_seconds())
            
            if execution_times:
                avg_execution_time = sum(execution_times) / len(execution_times)
        
        return {
            "total_traces": total_traces,
            "successful_traces": successful_traces,
            "success_rate": successful_traces / total_traces if total_traces > 0 else 0,
            "total_tokens": total_tokens,
            "avg_tokens_per_trace": total_tokens / total_traces if total_traces > 0 else 0,
            "total_api_calls": total_api_calls,
            "avg_api_calls_per_trace": total_api_calls / total_traces if total_traces > 0 else 0,
            "avg_execution_time": avg_execution_time
        }


# 全局轨迹捕获器实例
trace_capture = TraceCapture()
