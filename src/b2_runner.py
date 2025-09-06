# -*- coding: utf-8 -*-
"""B2 批量并发执行：读取 cases.jsonl，按 policy 跑任务并落盘。"""
from __future__ import annotations
import argparse
import os
import json
import sys
import concurrent.futures as futures
from typing import List, Dict

# 支持直接运行
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
    from src.core.model_adapter import OpenAIAdapter, KimiAdapter
    from src.core.toolbus import LocalBus
    from src.core.sink import FileSink
    from src.core.react_engine import ReactEngine, ReactConfig
else:
    from .core.model_adapter import OpenAIAdapter, KimiAdapter
    from .core.toolbus import LocalBus
    from .core.sink import FileSink
    from .core.react_engine import ReactEngine, ReactConfig

try:
    import yaml
except ImportError:
    print("警告: yaml 库未安装，将使用默认配置")
    yaml = None


def load_policy(path: str) -> dict:
    if not os.path.exists(path):
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


def read_cases(path: str) -> List[Dict]:
    out = []
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                out.append(json.loads(line))
    return out


def run_one(case: Dict, policy: Dict, out_root: str) -> Dict:
    case_id = case.get("id") or "unknown"
    policy_name = policy.get("name", "v1")
    # 输出结构：<out_root>/<policy>/<case_id>/<run_id>/
    out_base = os.path.join(out_root, policy_name, case_id)
    os.makedirs(out_base, exist_ok=True)

    adapter = KimiAdapter(model=policy.get("model", "moonshot-v1-8k"), temperature=float(policy.get("temperature", 0.2)))
    bus = LocalBus(allow=policy.get("tools", {}).get("allow"))
    
    from .core.react_engine import ReactConfig
    config = ReactConfig(
        max_steps=int(policy.get("max_steps", 8)),
        redact_secrets=bool(policy.get("redact_thought", True))
    )
    engine = ReactEngine(adapter, bus, config)
    run = engine.run(case["prompt"])
    return {"id": case_id, "run_id": getattr(run, 'run_id', 'unknown'), "metrics": run.metrics, "final": run.final_answer}


def main():
    ap = argparse.ArgumentParser(description="B2 批量执行")
    ap.add_argument("--cases", default="cases/cases.jsonl")
    ap.add_argument("--policy", default="cases/policies/v1.yaml")
    ap.add_argument("--max-concurrency", type=int, default=4)
    ap.add_argument("--out-base", default="runs")
    args = ap.parse_args()

    os.makedirs(args.out_base, exist_ok=True)
    policy = load_policy(args.policy)
    cases = read_cases(args.cases)

    results = []
    with futures.ThreadPoolExecutor(max_workers=args.max_concurrency) as ex:
        futs = [ex.submit(run_one, c, policy, args.out_base) for c in cases]
        for fu in futs:
            try:
                results.append(fu.result())
            except Exception as e:
                results.append({"error": str(e)})

    out_json = os.path.join(args.out_base, f"batch_results_{policy.get('name', 'v1')}.json")
    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)
    print("写入批量结果：", out_json)


if __name__ == "__main__":
    main()