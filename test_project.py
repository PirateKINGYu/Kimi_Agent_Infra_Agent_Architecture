#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B1 React Engine 测试脚本
"""

import sys
import os

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def test_basic_functionality():
    """测试基本功能"""
    print("=== B1 React Engine 基本功能测试 ===\n")
    
    try:
        # 测试导入
        print("1. 测试模块导入...")
        from src.core.model_adapter import ModelAdapter, OpenAIAdapter, KimiAdapter
        from src.core.toolbus import ToolBus, LocalBus
        from src.core.tools_local import TOOLS
        from src.core.trace import TraceStep, RunTrace
        from src.core.react_engine import ReactEngine, ReactConfig
        print("   ✓ 所有核心模块导入成功")
        
        # 测试工具总线
        print("\n2. 测试工具总线...")
        bus = LocalBus(allow=["calculator", "read_file", "write_file"])
        tools = bus.list_tools()
        print(f"   ✓ 可用工具: {list(tools.keys())}")
        
        # 测试计算器工具
        print("\n3. 测试计算器工具...")
        result = bus.call("calculator", "2 + 3 * 4")
        print(f"   ✓ 计算结果: {result}")
        
        # 测试文件工具
        print("\n4. 测试文件工具...")
        result = bus.call("write_file", "test.txt|Hello, B1 React Engine!")
        print(f"   ✓ 写入文件: {result}")
        
        result = bus.call("read_file", "test.txt")
        print(f"   ✓ 读取文件: {result}")
        
        # 清理测试文件
        try:
            os.remove("test.txt")
        except:
            pass
        
        print("\n5. 测试配置和引擎创建...")
        config = ReactConfig(max_steps=3, redact_secrets=False)
        print(f"   ✓ 配置创建成功: max_steps={config.max_steps}")
        
        # 模拟模型适配器（不需要真实API）
        class MockAdapter(ModelAdapter):
            def chat(self, messages):
                return "Thought: 这是一个测试\nAction: Final Answer\nAction Input: 测试成功完成", {
                    "latency_s": 0.1, 
                    "usage": {"total_tokens": 100}
                }
            
            def name(self):
                return "mock-model"
        
        mock_model = MockAdapter()
        engine = ReactEngine(mock_model, bus, config)
        print("   ✓ 引擎创建成功")
        
        print("\n6. 测试轨迹记录...")
        import time
        trace = RunTrace(
            task="测试任务",
            run_dir="test_run",
            start_time=time.time()
        )
        print(f"   ✓ 轨迹创建成功: {trace.task}")
        
        print("\n🎉 所有基本功能测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_engine_run():
    """测试引擎完整运行"""
    print("\n=== 测试引擎运行 ===\n")
    
    try:
        # 创建模拟模型
        class MockAdapter:
            def chat(self, messages):
                # 模拟一个简单的计算任务
                return """Thought: 我需要计算 2 + 3
Action: calculator
Action Input: 2 + 3""", {
                    "latency_s": 0.1,
                    "usage": {"total_tokens": 50}
                }
            
            def name(self):
                return "mock-gpt"
        
        from src.core.toolbus import LocalBus
        from src.core.react_engine import ReactEngine, ReactConfig
        
        model = MockAdapter()
        tools = LocalBus(allow=["calculator"])
        config = ReactConfig(max_steps=2)
        
        engine = ReactEngine(model, tools, config)
        
        # 运行一个简单任务
        print("运行任务: 计算 2 + 3")
        trace = engine.run("计算 2 + 3", "test_runs/calculation")
        
        print(f"任务完成!")
        print(f"步骤数: {len(trace.steps)}")
        print(f"最终答案: {trace.final_answer}")
        
        # 清理
        import shutil
        try:
            shutil.rmtree("test_runs", ignore_errors=True)
        except:
            pass
        
        return True
        
    except Exception as e:
        print(f"❌ 引擎运行测试失败: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("B1 React Engine 测试开始...\n")
    
    success1 = test_basic_functionality()
    success2 = test_engine_run()
    
    if success1 and success2:
        print("\n🎉 所有测试通过！项目可以正常使用。")
        print("\n下一步:")
        print("1. 设置环境变量 (复制 .env.example 为 .env)")
        print("2. 安装依赖: pip install -r requirements.txt")
        print("3. 运行单任务: python -m src.b1_cli --task '你的任务'")
        print("4. 运行批量任务: python -m src.b2_runner")
    else:
        print("\n❌ 测试未完全通过，请检查问题。")
        sys.exit(1)
