# -*- coding: utf-8 -*-
"""B2 自动评分：基于规则的轻量打分与汇总。"""
from __future__ import annotations
import argparse
import os
import json
import glob
import sys
from typing import Dict, Any

# 支持直接运行
if __name__ == "__main__" and __package__ is None:
    sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# 加强：用目录结构或 trace.json 的 case_id 对齐用例；新增 exists_file 规则


def load_run_trace(run_dir: str) -> Dict[str, Any]:
    p = os.path.join(run_dir, "trace.json")
    with open(p, "r", encoding="utf-8") as f:
        return json.load(f)


def infer_case_from_dir(run_dir: str) -> str:
    # 目录结构：.../<policy>/<case_id>/<run_id>
    return os.path.basename(os.path.dirname(run_dir))


def check_rules(run: Dict[str, Any], expect: Dict[str, Any], base_dir: str) -> Dict[str, Any]:
    ok = True
    details = []
    final = (run.get("final_answer") or "")
    steps = run.get("steps") or []

    if "exists_file" in expect:
        p = os.path.join(base_dir, expect["exists_file"]["path"])
        hit = os.path.exists(p)
        ok = ok and hit
        details.append({"exists_file": expect["exists_file"], "pass": hit})

    if "must_contain" in expect:
        for kw in expect["must_contain"]:
            hit = (kw in final)
            ok = ok and hit
            details.append({"must_contain": kw, "pass": hit})

    if "max_steps" in expect:
        hit = len(steps) <= int(expect["max_steps"])
        ok = ok and hit
        details.append({"max_steps": expect["max_steps"], "actual": len(steps), "pass": hit})

    if "eq_file" in expect:
        p = os.path.join(base_dir, expect["eq_file"]["path"])  # 目标文件应在该 run 目录内
        try:
            with open(p, "r", encoding="utf-8") as f:
                val = f.read().strip()
            hit = (val == str(expect["eq_file"]["value"]))
        except Exception:
            hit = False
        ok = ok and hit
        details.append({"eq_file": expect["eq_file"], "pass": hit})

    return {"pass": ok, "details": details}


def main():
    ap = argparse.ArgumentParser(description="B2 规则评分")
    ap.add_argument("--runs", required=True, help="批量输出根目录（包含 <policy>/<case>/<run> 结构）")
    ap.add_argument("--out", default="summary.csv")
    ap.add_argument("--cases", default="cases/cases.jsonl")
    args = ap.parse_args()

    # 读取用例期望
    case_expect = {}
    with open(args.cases, "r", encoding="utf-8") as f:
        for line in f:
            if line.strip():
                obj = json.loads(line)
                case_expect[obj["id"]] = obj.get("expect", {})

    # 遍历 runs/<policy>/<case>/<run>
    rows = ["policy,case_id,run_id,pass,total_tokens,tool_calls,errors,steps_to_success"]
    for d in sorted(glob.glob(os.path.join(args.runs, "*", "*", "*"))):
        tj = os.path.join(d, "trace.json")
        if not os.path.exists(tj):
            continue
        run = load_run_trace(d)
        case_id = run.get("case_id") or infer_case_from_dir(d)
        expect = case_expect.get(case_id, {})
        res = check_rules(run, expect, d)
        m = run.get("metrics", {})
        policy = run.get("policy", "")
        rows.append(f"{policy},{case_id},{os.path.basename(d)},{res['pass']},{m.get('total_tokens')},{m.get('tool_calls')},{m.get('errors')},{m.get('steps_to_success')}")

    with open(args.out, "w", encoding="utf-8") as f:
        f.write("\n".join(rows))
    print("写入评分汇总：", args.out)


if __name__ == "__main__":
    main()