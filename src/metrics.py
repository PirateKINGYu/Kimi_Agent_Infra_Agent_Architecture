
import json, re, statistics

def redact_pii(text: str) -> str:
    # very rough demo: mask emails / phone-like sequences
    text = re.sub(r"[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Za-z]{2,}", "[EMAIL]", text)
    text = re.sub(r"\b\d{3,4}[- ]?\d{3,4}[- ]?\d{3,4}\b", "[PHONE]", text)
    return text

def aggregate(reports):
    out = {
        "total": len(reports),
        "ok": sum(1 for r in reports if r["status"] == "ok"),
        "stalled": sum(1 for r in reports if r["status"] == "stalled"),
        "max_steps": sum(1 for r in reports if r["status"] == "max_steps"),
        "avg_steps": round(statistics.mean(r["steps"] for r in reports), 3),
        "avg_latency_s": round(statistics.mean(r["latency_s"] for r in reports), 3),
        "avg_token_est": round(statistics.mean(r["token_est_total"] for r in reports), 1),
        "avg_tool_calls": round(statistics.mean(r["tool_calls"] for r in reports), 2),
    }
    return out

def score(report, case):
    """Very simple auto scoring:
       - if 'expect' in case → substring match in final_answer
       - file checks ignored here (batch runner handles)
    """
    final = (report.get("final_answer") or "").lower()
    exp = (case.get("expect") or "").lower()
    if exp:
        return 1.0 if exp in final else 0.0
    return 0.0
