"""
MCP 工具集成模块
实现基础工具的 MCP 协议封装
"""
import json
import time
import requests
from typing import Dict, Any, List
from datetime import datetime
from langchain.tools import Tool


class MCPTool:
    """MCP 协议工具基类"""
    
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.created_at = datetime.now()
    
    def execute(self, **kwargs) -> Dict[str, Any]:
        """执行工具，返回标准化结果"""
        start_time = time.time()
        try:
            result = self._execute(**kwargs)
            return {
                "success": True,
                "result": result,
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
        except Exception as e:
            return {
                "success": False,
                "error": str(e),
                "execution_time": time.time() - start_time,
                "timestamp": datetime.now().isoformat()
            }
    
    def _execute(self, **kwargs):
        """具体的执行逻辑，由子类实现"""
        raise NotImplementedError


class SearchTool(MCPTool):
    """搜索工具"""
    
    def __init__(self):
        super().__init__(
            name="search",
            description="在网络上搜索信息，输入查询关键词"
        )
    
    def _execute(self, query: str) -> str:
        """模拟搜索功能"""
        # 这里可以集成真实的搜索API
        return f"搜索结果：关于'{query}'的相关信息..."


class CalculatorTool(MCPTool):
    """计算器工具"""
    
    def __init__(self):
        super().__init__(
            name="calculator",
            description="执行数学计算，输入数学表达式"
        )
    
    def _execute(self, expression: str) -> float:
        """安全的数学计算"""
        try:
            # 简单的安全检查
            allowed_chars = set('0123456789+-*/.() ')
            if not all(c in allowed_chars for c in expression):
                raise ValueError("表达式包含不安全字符")
            
            result = eval(expression)
            return result
        except Exception as e:
            raise ValueError(f"计算错误: {e}")


class FileOperationTool(MCPTool):
    """文件操作工具"""
    
    def __init__(self):
        super().__init__(
            name="file_operation",
            description="执行文件操作，支持读取、写入、列表等操作"
        )
    
    def _execute(self, operation: str, path: str, content: str = None) -> str:
        """执行文件操作"""
        import os
        
        if operation == "read":
            with open(path, 'r', encoding='utf-8') as f:
                return f.read()
        
        elif operation == "write":
            with open(path, 'w', encoding='utf-8') as f:
                f.write(content or "")
            return f"文件已写入: {path}"
        
        elif operation == "list":
            files = os.listdir(path)
            return f"目录内容: {', '.join(files)}"
        
        else:
            raise ValueError(f"不支持的操作: {operation}")


class MCPToolManager:
    """MCP 工具管理器"""
    
    def __init__(self):
        self.tools = {}
        self._register_default_tools()
    
    def _register_default_tools(self):
        """注册默认工具"""
        default_tools = [
            SearchTool(),
            CalculatorTool(),
            FileOperationTool()
        ]
        
        for tool in default_tools:
            self.register_tool(tool)
    
    def register_tool(self, tool: MCPTool):
        """注册工具"""
        self.tools[tool.name] = tool
    
    def get_tool(self, name: str) -> MCPTool:
        """获取工具"""
        if name not in self.tools:
            raise ValueError(f"工具不存在: {name}")
        return self.tools[name]
    
    def list_tools(self) -> List[Dict[str, str]]:
        """列出所有可用工具"""
        return [
            {
                "name": tool.name,
                "description": tool.description
            }
            for tool in self.tools.values()
        ]
    
    def to_langchain_tools(self) -> List[Tool]:
        """转换为 LangChain 工具格式"""
        langchain_tools = []
        
        for tool in self.tools.values():
            def make_func(t):
                def func(input_str: str) -> str:
                    try:
                        # 解析输入参数
                        if input_str.startswith('{'):
                            kwargs = json.loads(input_str)
                        else:
                            # 简单字符串输入
                            if t.name == "search":
                                kwargs = {"query": input_str}
                            elif t.name == "calculator":
                                kwargs = {"expression": input_str}
                            else:
                                kwargs = {"input": input_str}
                        
                        result = t.execute(**kwargs)
                        return json.dumps(result, ensure_ascii=False, indent=2)
                    except Exception as e:
                        return f"工具执行错误: {e}"
                return func
            
            langchain_tool = Tool(
                name=tool.name,
                description=tool.description,
                func=make_func(tool)
            )
            langchain_tools.append(langchain_tool)
        
        return langchain_tools
