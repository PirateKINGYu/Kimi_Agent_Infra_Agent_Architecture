
import json
import matplotlib.pyplot as plt

def plot_trace(trace_path: str, out_png: str):
    with open(trace_path, "r", encoding="utf-8") as f:
        trace = json.load(f)
    steps = trace["steps"]
    xs = [s["step"] for s in steps]
    durs = [max(1e-3, s["t_end"] - s["t_start"]) for s in steps]
    labels = [ (s.get("action") or "think") for s in steps ]

    plt.figure(figsize=(8, 3))
    plt.bar(xs, durs)
    plt.xticks(xs, labels, rotation=45, ha="right")
    plt.xlabel("Step (action)")
    plt.ylabel("Duration (s)")
    plt.title("ReAct Trace Duration by Step")
    plt.tight_layout()
    plt.savefig(out_png, dpi=150)
    plt.close()
