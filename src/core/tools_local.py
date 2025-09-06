# -*- coding: utf-8 -*-
"""本地工具：计算/文件/搜索。注意安全约束与工作目录绑定。"""
from __future__ import annotations
import os, json, math, urllib.parse, urllib.request
from typing import Dict, Callable


# 运行时工作目录（由上层注入）；所有文件操作相对该目录
_BASE_DIR = "."


def set_base_dir(path: str):
    """由上层注入每个 run 的工作目录。"""
    global _BASE_DIR
    _BASE_DIR = path


# 计算器：严格白名单，避免任意代码执行
_ALLOWED = {k: getattr(math, k) for k in dir(math) if not k.startswith("_")}
_ALLOWED["abs"] = abs


def tool_calculator(expr: str) -> str:
    """计算器：严格白名单，避免任意代码执行"""
    code = compile(expr, "<calc>", "eval")
    for name in code.co_names:
        if name not in _ALLOWED:
            raise ValueError(f"不允许的名称: {name}")
    return str(eval(code, {"__builtins__": {}}, _ALLOWED))


# 文件操作安全：仅允许相对路径且禁止 ..
def _ensure_safe_path(path: str) -> str:
    if os.path.isabs(path) or ".." in os.path.normpath(path):
        raise ValueError("不允许的路径：仅允许相对路径且禁止 ..")
    return path


def tool_read_file(path: str) -> str:
    """读取文件内容"""
    p = _ensure_safe_path(path)
    full = os.path.join(_BASE_DIR, p)
    with open(full, "r", encoding="utf-8", errors="ignore") as f:
        return f.read()


def tool_write_file(payload: str) -> str:
    """写入文件内容"""
    # 支持 JSON payload 或 "path|text" 简写
    if payload.strip().startswith("{"):
        obj = json.loads(payload)
        path, text = obj["path"], obj["text"]
    else:
        path, text = payload.split("|", 1)
    p = _ensure_safe_path(path)
    full = os.path.join(_BASE_DIR, p)
    os.makedirs(os.path.dirname(full) or ".", exist_ok=True)
    with open(full, "w", encoding="utf-8") as f:
        f.write(text)
    return f"写入 {len(text)} 字符到 {p}"


def tool_list_dir(path: str) -> str:
    """列出目录内容"""
    p = path or "."
    _ensure_safe_path(p)
    full = os.path.join(_BASE_DIR, p)
    if not os.path.exists(full):
        return f"路径不存在: {p}"
    return "\n".join(sorted(os.listdir(full)))


# 受限搜索：Wikipedia OpenSearch
def tool_web_search(query: str) -> str:
    """网页搜索"""
    q = urllib.parse.quote(query)
    url = (
        "https://en.wikipedia.org/w/api.php?action=opensearch&limit=3&namespace=0&format=json&search=" + q
    )
    with urllib.request.urlopen(url, timeout=15) as r:  # 演示用途
        data = json.loads(r.read().decode("utf-8", "ignore"))
    titles, descs, links = data[1], data[2], data[3]
    out = []
    for t, d, l in zip(titles, descs, links):
        out.append(f"- {t}: {d}\n  {l}")
    return "\n".join(out) or "<no results>"


# 注册表
TOOLS: Dict[str, Callable[[str], str]] = {
    "calculator": tool_calculator,
    "read_file": tool_read_file,
    "write_file": tool_write_file,
    "list_dir": tool_list_dir,
    "web_search": tool_web_search,
}