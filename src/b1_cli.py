# -*- coding: utf-8 -*-
"""B1 单任务 CLI：装配引擎 + 执行任务。"""
from __future__ import annotations
import argparse
import os
import json
import sys
from typing import Optional

# 支持直接运行
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.core.model_adapter import OpenAIAdapter, KimiAdapter, MockAdapter
    from src.core.toolbus import LocalBus, MCPBus
    from src.core.sink import FileSink, HttpSink
    from src.core.react_engine import ReactEngine, ReactConfig
else:
    from .core.model_adapter import OpenAIAdapter, KimiAdapter, MockAdapter
    from .core.toolbus import LocalBus, MCPBus
    from .core.sink import FileSink, HttpSink
    from .core.react_engine import ReactEngine, ReactConfig

try:
    import yaml
except ImportError:
    print("警告: yaml 库未安装，将使用默认配置")
    yaml = None


def load_policy(path: Optional[str]) -> dict:
    if not path or not os.path.exists(path):
        # 默认策略 - 使用 Kimi 模型
        return {
            "name": "v1", "model": "moonshot-v1-8k", "temperature": 0.2, "max_steps": 8, "redact_thought": True,
            "tools": {"allow": ["calculator", "read_file", "write_file", "list_dir", "web_search"]}
        }
    
    if yaml is None:
        print(f"无法加载 {path}，使用默认配置")
        return {
            "name": "v1", "model": "moonshot-v1-8k", "temperature": 0.2, "max_steps": 8, "redact_thought": True,
            "tools": {"allow": ["calculator", "read_file", "write_file", "list_dir", "web_search"]}
        }
    
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def main():
    ap = argparse.ArgumentParser(description="B1 单任务执行")
    ap.add_argument("--task", required=True, help="任务描述")
    ap.add_argument("--policy", default="cases/policies/v1.yaml", help="策略文件路径")
    ap.add_argument("--provider", default="kimi", choices=["openai", "kimi", "claude", "mock"], help="模型提供方")
    ap.add_argument("--sink", default="http", choices=["file", "http"], help="观测出口")
    ap.add_argument("--backend", default="http://127.0.0.1:8000", help="后端地址(当 sink=http)")
    ap.add_argument("--report-dir", default=None, help="输出基目录（FileSink）")
    args = ap.parse_args()

    policy = load_policy(args.policy)

    # 模型适配
    if args.provider == "openai":
        adapter = OpenAIAdapter(model=policy.get("model", "gpt-4o-mini"), temperature=float(policy.get("temperature", 0.2)))
    elif args.provider == "kimi":
        try:
            adapter = KimiAdapter(model=policy.get("model", "moonshot-v1-8k"), temperature=float(policy.get("temperature", 0.2)))
        except RuntimeError as e:
            print(f"Kimi API 初始化失败: {e}")
            print("自动切换到模拟模式...")
            adapter = MockAdapter(model="mock-kimi", temperature=float(policy.get("temperature", 0.2)))
    elif args.provider == "mock":
        adapter = MockAdapter(model="mock-model", temperature=float(policy.get("temperature", 0.2)))
    else:
        raise RuntimeError("当前支持 OpenAI、Kimi 和 Mock 适配器，Claude 可按需扩展")

    # 工具总线（优先 MCP，可切换）
    # bus = MCPBus(endpoint="...") # 预留
    tools_config = policy.get("tools") or {}
    allowed_tools = tools_config.get("allow") or ["calculator", "read_file", "write_file", "list_dir", "web_search"]
    bus = LocalBus(allow=allowed_tools)

    # 观测出口
    if args.sink == "http":
        sink = HttpSink(args.backend)
    else:
        sink = FileSink(base_dir=args.report_dir or "runs")

    # 创建引擎
    from .core.react_engine import ReactConfig
    config = ReactConfig(
        max_steps=int(policy.get("max_steps", 8)),
        redact_secrets=bool(policy.get("redact_thought", True))
    )
    engine = ReactEngine(adapter, bus, config, sink)

    # 执行任务
    run = engine.run(args.task)
    print("=== FINAL ANSWER ===\n" + (run.final_answer or "<none>"))
    print("\n=== METRICS ===\n" + json.dumps(run.metrics, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()