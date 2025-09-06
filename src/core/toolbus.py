# -*- coding: utf-8 -*-
"""工具总线：统一工具调用入口；支持本地与 MCP。"""
from __future__ import annotations
from typing import Any, Dict, Optional
import time
from . import tools_local


class ToolResult(dict):
    """规范化返回：{"ok":bool,"output":str,"error":str|None,"latency_s":float}"""
    pass


class ToolBus:
    def list_tools(self) -> Dict[str, Dict]:
        raise NotImplementedError
    
    def call(self, name: str, arg: Optional[str]) -> ToolResult:
        raise NotImplementedError


class LocalBus(ToolBus):
    """进程内工具调用，简单且可控。支持 per-run 工作目录。"""
    def __init__(self, allow: Optional[list] = None, workdir: Optional[str] = None):
        self._tools = tools_local.TOOLS
        self._allow = set(allow or self._tools.keys())
        self._workdir = workdir
        if workdir:
            tools_local.set_base_dir(workdir)
    
    def set_workdir(self, path: str):
        self._workdir = path
        tools_local.set_base_dir(path)
    
    def list_tools(self) -> Dict[str, Dict]:
        return {k: {"desc": self._tools[k].__doc__ or ""} for k in self._allow if k in self._tools}
    
    def call(self, name: str, arg: Optional[str]) -> ToolResult:
        if name not in self._allow:
            return ToolResult(ok=False, output="", error=f"工具未允许: {name}")
        if name not in self._tools:
            return ToolResult(ok=False, output="", error=f"工具不存在: {name}")
        t0 = time.time()
        try:
            out = self._tools[name](arg or "")
            return ToolResult(ok=True, output=out, error=None, latency_s=time.time()-t0)
        except Exception as e:
            return ToolResult(ok=False, output="", error=f"{type(e).__name__}: {e}", latency_s=time.time()-t0)


class MCPBus(ToolBus):
    """MCP 客户端占位：可按 MCP SDK 实现握手/列举/调用。"""
    def __init__(self, endpoint: str):
        self.endpoint = endpoint
    
    def list_tools(self) -> Dict[str, Dict]:
        raise NotImplementedError("MCPBus 需集成 MCP SDK 实现能力发现")
    
    def call(self, name: str, arg: Optional[str]) -> ToolResult:
        raise NotImplementedError("MCPBus 需集成 MCP SDK 实现调用")