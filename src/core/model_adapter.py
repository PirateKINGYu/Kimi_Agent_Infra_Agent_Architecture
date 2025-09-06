# -*- coding: utf-8 -*-
"""模型适配层：统一 chat 接口；默认实现 OpenAI 版本。
可扩展 Kimi/Claude，仅需实现同名接口。"""
from __future__ import annotations
from typing import Dict, List, Tuple
import os
import time

# 尝试加载 .env 文件
try:
    from dotenv import load_dotenv
    load_dotenv()
except ImportError:
    # 如果没有 python-dotenv，忽略
    pass

try:
    from openai import OpenAI  # 官方 SDK
except Exception:
    OpenAI = None


class ModelAdapter:
    """统一模型接口。"""
    def chat(self, messages: List[Dict[str, str]]) -> Tuple[str, Dict]:
        raise NotImplementedError
    
    def name(self) -> str:
        return self.__class__.__name__


class OpenAIAdapter(ModelAdapter):
    def __init__(self, model: str = "gpt-4o-mini", temperature: float = 0.2):
        if OpenAI is None:
            raise RuntimeError("openai SDK 未安装，请先 pip install openai")
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise RuntimeError("缺少 OPENAI_API_KEY 环境变量")
        self.client = OpenAI()
        self.model = model
        self.temperature = temperature

    def name(self) -> str:
        return self.model

    def chat(self, messages: List[Dict[str, str]]) -> Tuple[str, Dict]:
        # 简单调用 + 统计耗时与 token 使用
        t0 = time.time()
        resp = self.client.chat.completions.create(
            model=self.model, messages=messages, temperature=self.temperature
        )
        latency = time.time() - t0
        text = resp.choices[0].message.content or ""
        usage = getattr(resp, "usage", None)
        meta = {
            "latency_s": latency,
            "usage": {
                "prompt_tokens": getattr(usage, "prompt_tokens", None),
                "completion_tokens": getattr(usage, "completion_tokens", None),
                "total_tokens": getattr(usage, "total_tokens", None),
            },
        }
        return text, meta


# Kimi API 适配器实现
class KimiAdapter(ModelAdapter):
    def __init__(self, model: str = "moonshot-v1-8k", temperature: float = 0.2):
        try:
            from openai import OpenAI  # Kimi 使用兼容 OpenAI 的 SDK
        except ImportError:
            raise RuntimeError("openai SDK 未安装，请先 pip install openai")
        
        api_key = os.getenv("KIMI_API_KEY") or os.getenv("MOONSHOT_API_KEY")
        if not api_key:
            raise RuntimeError("缺少 KIMI_API_KEY 或 MOONSHOT_API_KEY 环境变量")
        
        base_url = os.getenv("KIMI_BASE_URL", "https://api.moonshot.cn/v1")
        
        self.client = OpenAI(
            api_key=api_key,
            base_url=base_url
        )
        self.model = model
        self.temperature = temperature

    def name(self) -> str:
        return self.model

    def chat(self, messages: List[Dict[str, str]]) -> Tuple[str, Dict]:
        # 调用 Kimi API + 统计耗时与 token 使用，支持重试
        import time
        
        max_retries = 3
        base_delay = 2  # 基础延迟秒数
        
        for attempt in range(max_retries):
            try:
                t0 = time.time()
                resp = self.client.chat.completions.create(
                    model=self.model, 
                    messages=messages, 
                    temperature=self.temperature
                )
                latency = time.time() - t0
                text = resp.choices[0].message.content or ""
                usage = getattr(resp, "usage", None)
                meta = {
                    "latency_s": latency,
                    "usage": {
                        "prompt_tokens": getattr(usage, "prompt_tokens", None),
                        "completion_tokens": getattr(usage, "completion_tokens", None),
                        "total_tokens": getattr(usage, "total_tokens", None),
                    },
                }
                return text, meta
                
            except Exception as e:
                error_msg = str(e)
                if "rate_limit" in error_msg.lower() or "429" in error_msg:
                    if attempt < max_retries - 1:  # 不是最后一次尝试
                        delay = base_delay * (2 ** attempt)  # 指数退避
                        print(f"速率限制，等待 {delay} 秒后重试... (尝试 {attempt + 1}/{max_retries})")
                        time.sleep(delay)
                        continue
                    else:
                        raise RuntimeError(f"达到最大重试次数，仍然遇到速率限制: {error_msg}")
                else:
                    # 其他错误直接抛出
                    raise e
        
        # 理论上不会到达这里
        raise RuntimeError("未知错误")


class ClaudeAdapter(ModelAdapter):
    def chat(self, messages):
        raise NotImplementedError("ClaudeAdapter 需按 API 文档实现")


# 模拟适配器（用于测试）
class MockAdapter(ModelAdapter):
    def __init__(self, model: str = "mock-model", temperature: float = 0.2):
        self.model = model
        self.temperature = temperature

    def name(self) -> str:
        return self.model

    def chat(self, messages: List[Dict[str, str]]) -> Tuple[str, Dict]:
        # 模拟 API 调用
        t0 = time.time()
        
        # 获取最后一条用户消息
        user_message = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_message = msg.get("content", "")
                break
        
        # 简单的模拟响应
        if "计算" in user_message or "Compute" in user_message:
            response = """Thought: 我需要使用计算器来计算这个数学表达式。
Action: calculator
Action Input: (23*19)+sqrt(144)"""
        elif "保存" in user_message or "save" in user_message:
            response = """Thought: 我需要将结果保存到文件中。
Action: write_file
Action Input: calc.txt
449"""
        else:
            response = """Thought: 我需要分析这个任务。
Action: Final Answer
Action Input: 我已经完成了任务分析。"""
        
        latency = time.time() - t0
        meta = {
            "latency_s": latency,
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 50,
                "total_tokens": 150,
            },
        }
        return response, meta