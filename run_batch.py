
import os, json, argparse, time
from concurrent.futures import ThreadPoolExecutor, as_completed
from src.engine import ReActEngine
from src.metrics import aggregate, score

def run_case(case, variant, out_dir):
    eng = ReActEngine(variant=variant, max_steps=8)
    case_dir = os.path.join(out_dir, f"{case['id']}_{variant}")
    os.makedirs(case_dir, exist_ok=True)
    # Pre-create any files needed
    if case.get("pre_file"):
        for p, content in case["pre_file"].items():
            os.makedirs(os.path.dirname(p) or ".", exist_ok=True)
            with open(p, "w", encoding="utf-8") as f:
                f.write(content)
    rep = eng.run(case["task"], out_dir=case_dir, suite_version=case.get("suite_version","v1"))

    # rudimentary check for file assertions
    passed = True
    chk = case.get("check") or {}
    if "file_exists" in chk:
        passed = passed and os.path.exists(chk["file_exists"])
    if "contains" in chk and "file_exists" in chk:
        try:
            with open(chk["file_exists"], "r", encoding="utf-8") as f:
                passed = passed and (chk["contains"] in f.read())
        except Exception:
            passed = False

    report_path = os.path.join(case_dir, "report.json")
    with open(report_path, "r", encoding="utf-8") as f:
        rep_content = json.load(f)
    rep_content["auto_score"] = score(rep_content, case)
    rep_content["assert_passed"] = bool(passed)
    with open(report_path, "w", encoding="utf-8") as f:
        json.dump(rep_content, f, ensure_ascii=False, indent=2)
    return rep_content

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--cases", type=str, default="tests/cases.jsonl")
    ap.add_argument("--variant", type=str, default="simple,deliberate")
    ap.add_argument("--out", type=str, default="artifacts")
    ap.add_argument("--max_workers", type=int, default=4)
    args = ap.parse_args()

    variants = [v.strip() for v in args.variant.split(",")]
    with open(args.cases, "r", encoding="utf-8") as f:
        cases = [json.loads(line) for line in f if line.strip()]

    overall = {}
    for v in variants:
        futures = []
        reports = []
        with ThreadPoolExecutor(max_workers=args.max_workers) as ex:
            for c in cases:
                futures.append(ex.submit(run_case, c, v, args.out))
            for fu in as_completed(futures):
                reports.append(fu.result())
        overall[v] = {
            "aggregate": aggregate(reports),
            "reports": reports
        }

    # write batch report
    os.makedirs(args.out, exist_ok=True)
    outp = os.path.join(args.out, "batch_report.json")
    with open(outp, "w", encoding="utf-8") as f:
        json.dump(overall, f, ensure_ascii=False, indent=2)
    print(json.dumps(overall, ensure_ascii=False, indent=2))

if __name__ == "__main__":
    main()
