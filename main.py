"""
主程序和命令行界面
演示 ReAct Agent 的完整功能
"""
import argparse
import json
from typing import Dict, Any

from react_agent import ReActAgent
from trace_capture import trace_capture
from visualization import visualizer


def demo_basic_usage():
    """基础使用演示"""
    print("=== ReAct Agent 基础演示 ===")
    
    agent = ReActAgent()
    
    # 示例查询
    queries = [
        "计算 25 * 34 + 128 的结果",
        "搜索关于人工智能的信息",
        "请帮我分析一下这两个数字：15和27的最大公约数"
    ]
    
    for i, query in enumerate(queries, 1):
        print(f"\n--- 查询 {i}: {query} ---")
        
        result = agent.run(query)
        print(f"结果: {result}")
        
        # 显示轨迹信息
        trace_info = agent.get_trace_info()
        print(f"轨迹信息: {json.dumps(trace_info, ensure_ascii=False, indent=2)}")
    
    # 显示总体统计
    print("\n=== 总体统计 ===")
    stats = agent.get_statistics()
    print(json.dumps(stats, ensure_ascii=False, indent=2))


def demo_visualization():
    """可视化演示"""
    print("\n=== 可视化分析演示 ===")
    
    # 刷新数据
    visualizer.refresh_data()
    
    # 生成各种图表
    print("生成执行时间线图...")
    visualizer.plot_execution_timeline()
    
    print("生成性能指标图...")
    visualizer.plot_performance_metrics()
    
    print("分析工具使用情况...")
    tool_stats = visualizer.analyze_tool_usage()
    if tool_stats:
        print("工具使用统计:")
        for tool, stats in tool_stats.items():
            print(f"  {tool}: 使用{stats['count']}次, 成功率{stats['success_rate']:.2%}")
    
    print("创建交互式仪表板...")
    visualizer.create_interactive_dashboard()
    
    # 导出报告
    visualizer.export_report("demo_report.json")


def interactive_mode():
    """交互模式"""
    print("=== ReAct Agent 交互模式 ===")
    print("输入 'quit' 退出，输入 'stats' 查看统计，输入 'viz' 进行可视化分析")
    
    agent = ReActAgent()
    
    while True:
        query = input("\n请输入您的问题: ").strip()
        
        if query.lower() == 'quit':
            break
        elif query.lower() == 'stats':
            stats = agent.get_statistics()
            print(json.dumps(stats, ensure_ascii=False, indent=2))
            continue
        elif query.lower() == 'viz':
            demo_visualization()
            continue
        elif not query:
            continue
        
        print("\n正在处理...")
        result = agent.run(query)
        print(f"\n回答: {result}")
        
        # 显示简要轨迹信息
        trace_info = agent.get_trace_info()
        print(f"执行了 {trace_info.get('steps_count', 0)} 个步骤，"
              f"调用了 {trace_info.get('tool_calls_count', 0)} 次工具")


def export_trace(trace_id: str, format: str = "json"):
    """导出指定轨迹"""
    try:
        trace_data = trace_capture.export_trace(trace_id, format)
        filename = f"trace_{trace_id}_{format}"
        
        with open(filename, 'w', encoding='utf-8') as f:
            f.write(trace_data)
        
        print(f"轨迹已导出到: {filename}")
    except Exception as e:
        print(f"导出失败: {e}")


def list_traces():
    """列出所有轨迹"""
    traces = trace_capture.get_all_traces()
    
    if not traces:
        print("没有轨迹记录")
        return
    
    print("=== 轨迹列表 ===")
    for i, trace in enumerate(traces, 1):
        print(f"{i}. ID: {trace.trace_id}")
        print(f"   查询: {trace.query}")
        print(f"   状态: {'成功' if trace.success else '失败'}")
        print(f"   时间: {trace.start_time}")
        print(f"   步骤: {len(trace.steps)}, 工具调用: {len(trace.tool_calls)}")
        print()


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="ReAct Agent 演示程序")
    parser.add_argument("--mode", choices=["demo", "interactive", "viz"], 
                       default="demo", help="运行模式")
    parser.add_argument("--export-trace", type=str, help="导出指定轨迹ID")
    parser.add_argument("--list-traces", action="store_true", help="列出所有轨迹")
    
    args = parser.parse_args()
    
    if args.export_trace:
        export_trace(args.export_trace)
    elif args.list_traces:
        list_traces()
    elif args.mode == "demo":
        demo_basic_usage()
        demo_visualization()
    elif args.mode == "interactive":
        interactive_mode()
    elif args.mode == "viz":
        demo_visualization()


if __name__ == "__main__":
    main()
