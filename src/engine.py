
import json, time, os, re
from dataclasses import dataclass, field, asdict
from typing import Callable, Dict, Any, List, Optional

# -----------------------
# Tools (pure stdlib)
# -----------------------
def tool_calculator(expression: str) -> str:
    """
    Safe-ish arithmetic evaluator: digits + operators + parentheses.
    """
    expr = expression.replace(" ", "")
    if not re.fullmatch(r"[0-9\+\-\*\/\(\)\.]+", expr):
        raise ValueError("Calculator only supports + - * / ( ) and digits.")
    # Very small safety: evaluate with Python but restrict builtins.
    return str(eval(expr, {"__builtins__": {}}, {}))

def tool_file_write(payload: str) -> str:
    """
    Input format: 'path|content'
    """
    if "|" not in payload:
        raise ValueError("file_write expects 'path|content'")
    path, content = payload.split("|", 1)
    path = path.strip()
    os.makedirs(os.path.dirname(path) or ".", exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    return f"wrote {len(content)} chars to {path}"

def tool_file_read(path: str) -> str:
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

def tool_file_list(path: str) -> str:
    if not os.path.isdir(path):
        return "[]"
    return json.dumps(sorted(os.listdir(path)))

def tool_mock_search(query: str) -> str:
    """
    Offline mock search over a tiny in-memory corpus for demo purpose.
    """
    corpus = {
        "capital of france": "Paris is the capital of France.",
        "kimi agent": "Kimi Agent focuses on agent infra and products.",
        "react pattern": "ReAct = Reasoning + Acting with tool-use loops."
    }
    q = query.lower().strip()
    best = None
    for k, v in corpus.items():
        if k in q:
            best = v
            break
    return best or "No result in mock corpus."

# -----------------------
# Data models
# -----------------------
@dataclass
class StepTrace:
    step: int
    thought: str
    action: Optional[str] = None
    input: Optional[str] = None
    observation: Optional[str] = None
    error: Optional[str] = None
    t_start: float = 0.0
    t_end: float = 0.0
    token_est: int = 0

@dataclass
class RunTrace:
    task: str
    policy_variant: str
    suite_version: str = "v1"
    steps: List[StepTrace] = field(default_factory=list)
    started_at: float = 0.0
    ended_at: float = 0.0
    status: str = "running"
    final_answer: Optional[str] = None
    reason: Optional[str] = None
    tool_calls: int = 0
    token_est_total: int = 0

# -----------------------
# Policy (pluggable)
# -----------------------
class SimpleReActPolicy:
    """
    A minimal rule-based policy to emulate ReAct. It yields 'thought' and 'action'
    (tool_name, tool_input) pairs until Finish.
    Two variants: 'simple' and 'deliberate' (adds a planning thought).
    """
    def __init__(self, variant: str = "simple"):
        self.variant = variant

    def decide(self, task: str, steps: List[StepTrace]) -> dict:
        """
        Return dict: {"finish": bool, "thought": str,
                      "action": Optional[tuple(tool_name, tool_input)],
                      "final_answer": Optional[str]}
        """
        text = task.lower()

        # If we already found a numeric result in earlier observation, finish.
        if steps:
            last_obs = (steps[-1].observation or "").strip()
            if last_obs and "final=" in last_obs:
                val = last_obs.split("final=", 1)[-1].strip()
                return {"finish": True, "thought": "I have computed the result.", "final_answer": val}

        # Deliberate adds a planning step at the beginning.
        if self.variant == "deliberate" and len(steps) == 0:
            return {"finish": False, "thought": "Plan: identify subgoals and choose a tool.",
                    "action": None}

        # Arithmetic?
        if re.search(r"\d+\s*[\+\-\*\/]\s*\d+", text):
            expr = re.findall(r"[\d\.\s\+\-\*\/\(\)]+", task)[0]
            return {"finish": False,
                    "thought": f"Compute the expression {expr.strip()} by calculator.",
                    "action": ("calculator", expr)}

        # File write?
        m = re.search(r"(?:write|保存|写入).*(?:to|到)\s+([^\s，,]+).*?(?:'|\")?(.+?)(?:'|\")?$", task, re.I)
        if m:
            path = m.group(1)
            content = m.group(2)
            payload = f"{path}|{content}"
            return {"finish": False,
                    "thought": f"Persist content into file {path}.",
                    "action": ("file_write", payload)}

        # "create file xxx with yyy"
        m2 = re.search(r"create (?:a )?file ([^\s]+) with (.+)", task, re.I)
        if m2:
            path = m2.group(1)
            content = m2.group(2)
            payload = f"{path}|{content}"
            return {"finish": False,
                    "thought": f"Create file {path}.",
                    "action": ("file_write", payload)}

        # Search?
        if any(k in text for k in ["search", "who is", "capital of", "react"]):
            q = task
            return {"finish": False,
                    "thought": "Use search to gather facts.",
                    "action": ("search", q)}

        # Read file?
        if "read" in text and ".txt" in text:
            path = re.findall(r"([A-Za-z0-9_\-\/\.]+\.txt)", task)
            if path:
                return {"finish": False,
                        "thought": f"Read file {path[0]}.",
                        "action": ("file_read", path[0])}

        # Default: finish with best-so-far (if any)
        return {"finish": True, "thought": "No action needed; produce answer.",
                "final_answer": "Done."}

# -----------------------
# Engine
# -----------------------
class ReActEngine:
    def __init__(self, variant: str = "simple", max_steps: int = 8):
        self.variant = variant
        self.max_steps = max_steps
        self.policy = SimpleReActPolicy(variant=variant)
        # tool registry
        self.tools = {
            "calculator": tool_calculator,
            "file_write": tool_file_write,
            "file_read": tool_file_read,
            "file_list": tool_file_list,
            "search": tool_mock_search,
        }

    def _token_est(self, *txts: str) -> int:
        return int(sum(len(t) for t in txts) / 4)

    def run(self, task: str, out_dir: str = "artifacts", suite_version: str = "v1") -> dict:
        os.makedirs(out_dir, exist_ok=True)
        trace = RunTrace(task=task, policy_variant=self.variant, suite_version=suite_version)
        trace.started_at = time.time()

        recent_actions = []
        for step_id in range(1, self.max_steps + 1):
            dec = self.policy.decide(task, trace.steps)
            if dec.get("finish"):
                thought = dec.get("thought", "")
                st = StepTrace(step=step_id, thought=thought, t_start=time.time())
                st.t_end = time.time()
                st.token_est = self._token_est(thought)
                trace.steps.append(st)
                trace.final_answer = dec.get("final_answer", trace.final_answer)
                trace.status = "ok"
                trace.reason = trace.reason or "finished"
                break

            thought = dec.get("thought", "")
            action = dec.get("action")
            st = StepTrace(step=step_id, thought=thought, t_start=time.time())
            st.token_est = self._token_est(thought)

            obs = None
            err = None
            if action:
                tool_name, tool_input = action
                st.action = tool_name
                st.input = tool_input
                recent_actions.append(tool_name)
                if len(recent_actions) > 3:
                    recent_actions.pop(0)

                try:
                    func = self.tools[tool_name]
                    obs = func(tool_input)
                    trace.tool_calls += 1
                except Exception as e:
                    err = f"{type(e).__name__}: {e}"

            st.observation = obs
            st.error = err
            st.t_end = time.time()
            trace.steps.append(st)
            trace.token_est_total += st.token_est

            # Heuristic: if same tool repeated 3 times with no new observation info → loop
            if len(recent_actions) == 3 and len(set(recent_actions)) == 1:
                trace.status = "stalled"
                trace.reason = f"loop detected on tool '{recent_actions[-1]}'"
                break

            # If calculator produced a number, store as final and let policy finalize in next step
            if st.action == "calculator" and st.error is None:
                st.observation = f"final={st.observation}"

        else:
            trace.status = "max_steps"
            trace.reason = "max steps reached"

        trace.ended_at = time.time()

        # Persist
        out_trace = os.path.join(out_dir, "trace.json")
        with open(out_trace, "w", encoding="utf-8") as f:
            json.dump(asdict(trace), f, ensure_ascii=False, indent=2)

        # Small run report
        report = {
            "task": task,
            "policy_variant": self.variant,
            "status": trace.status,
            "reason": trace.reason,
            "final_answer": trace.final_answer,
            "steps": len(trace.steps),
            "tool_calls": trace.tool_calls,
            "token_est_total": trace.token_est_total,
            "latency_s": round(trace.ended_at - trace.started_at, 4)
        }
        out_report = os.path.join(out_dir, "report.json")
        with open(out_report, "w", encoding="utf-8") as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        return report
