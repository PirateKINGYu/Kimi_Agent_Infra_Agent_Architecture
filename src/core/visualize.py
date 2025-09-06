# -*- coding: utf-8 -*-
"""生成单文件 HTML 报告：时间线卡片 + 顶部指标 + 关键字过滤。"""
from __future__ import annotations
from typing import List
from html import escape
from .trace import RunTrace, TraceStep


_HTML_TEMPLATE = """
<!doctype html><html><head><meta charset="utf-8"><title>Agent Trace</title>
<style>
body{font-family:system-ui,-apple-system,BlinkMacSystemFont,Segoe UI,Roboto,Helvetica,Arial,sans-serif;padding:16px}
.step{border:1px solid #e5e5e5;border-radius:12px;padding:12px;margin:10px 0;box-shadow:0 1px 3px rgba(0,0,0,.05)}
.badge{display:inline-block;background:#f6f6f6;border-radius:8px;padding:2px 8px;margin-right:6px;font-size:12px}
pre{white-space:pre-wrap;background:#fafafa;border-radius:8px;padding:8px}
.controls{position:sticky;top:0;background:#fff;padding:8px;border-bottom:1px solid #eee;margin:-16px -16px 12px}
small{color:#666}
</style></head><body>
<div class="controls">
<strong>Task:</strong> {task}<br>
<small>Model: {model} | Policy: {policy} | Created: {created}</small><br>
<small>Metrics — tokens: {tokens}, tool_calls: {tool_calls}, errors: {errors}, total_latency_s: {lat}</small>
<div><label>Filter: <input id="q" oninput="f()" placeholder="查找步骤文本"></label></div>
</div>
<div id="steps">{steps}</div>
<script>
function f(){const q=document.getElementById('q').value.toLowerCase();
for(const el of document.querySelectorAll('.step')){el.style.display=el.innerText.toLowerCase().includes(q)?'':'none'}}
</script>
</body></html>
"""


def _block(s: TraceStep) -> str:
    return (
        f"<div class='step'>"
        f"<div><span class='badge'>Step {s.step}</span>"
        f"<span class='badge'>lat: {s.latency_s:.2f}s</span>"
        f"<span class='badge'>tool: {escape(str(s.action or '—'))}</span>"
        f"<span class='badge'>err: {escape(str(bool(s.error)))}</span></div>"
        f"<pre><b>Thought</b>\n{escape(s.thought or '')}</pre>"
        f"<pre><b>Action</b>\n{escape(str(s.action or ''))}\n\n<b>Action Input</b>\n{escape(str(s.action_input or ''))}</pre>"
        f"<pre><b>Observation</b>\n{escape(str(s.observation or ''))}</pre>"
        f"</div>"
    )


def render_html(run: RunTrace) -> str:
    steps_html = "\n".join(_block(s) for s in run.steps)
    m = run.metrics or {}
    return _HTML_TEMPLATE.format(
        task=escape(run.task), model=escape(getattr(run, 'model', '')), policy=escape(getattr(run, 'policy', '')), 
        created=escape(getattr(run, 'created_at', '')),
        tokens=m.get("total_tokens", 0), tool_calls=m.get("tool_calls", 0), errors=m.get("errors", 0), 
        lat=m.get("total_latency_s", 0.0),
        steps=steps_html,
    )