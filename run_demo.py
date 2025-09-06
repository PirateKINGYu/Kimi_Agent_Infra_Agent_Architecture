
import os, json, argparse
from src.engine import ReActEngine
from src.viz import plot_trace

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--task", type=str, default="Compute 12*7 then write to result.txt 'The result is 84'")
    ap.add_argument("--variant", type=str, default="simple")
    ap.add_argument("--out", type=str, default="artifacts")
    args = ap.parse_args()

    eng = ReActEngine(variant=args.variant, max_steps=8)
    rep = eng.run(args.task, out_dir=args.out, suite_version="v1")

    trace_path = os.path.join(args.out, "trace.json")
    png_path = os.path.join(args.out, "trace.png")
    try:
        plot_trace(trace_path, png_path)
    except Exception as e:
        print("viz error:", e)

    print(json.dumps(rep, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
