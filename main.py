#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
B1 React Engine 主入口脚本
使用示例:
  python main.py b1 --task "计算 2+3"
  python main.py b2 --cases cases/cases.jsonl
  python main.py eval --runs runs
  python main.py server
"""

import sys
import os
import argparse

# 添加项目根目录到 Python 路径
project_root = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, project_root)

def run_b1():
    """运行 B1 单任务"""
    from src.b1_cli import main
    main()

def run_b2():
    """运行 B2 批量任务"""
    from src.b2_runner import main
    main()

def run_eval():
    """运行评估"""
    from src.b2_eval import main
    main()

def run_server():
    """运行后端服务器"""
    try:
        from backend.app import app
        import uvicorn
        print("启动 B1 React Engine 后端服务...")
        print("访问地址: http://localhost:8000")
        uvicorn.run(app, host="0.0.0.0", port=8000)
    except ImportError as e:
        print(f"无法启动服务器: {e}")
        print("请安装依赖: pip install fastapi uvicorn")

def run_test():
    """运行测试"""
    import subprocess
    return subprocess.call([sys.executable, "test_project.py"])

def main():
    parser = argparse.ArgumentParser(description="B1 React Engine 主程序")
    subparsers = parser.add_subparsers(dest='command', help='可用命令')
    
    # B1 子命令
    b1_parser = subparsers.add_parser('b1', help='运行单任务')
    b1_parser.add_argument('--task', required=True, help='任务描述')
    b1_parser.add_argument('--policy', default="policies/v1.yaml", help='策略文件')
    b1_parser.add_argument('--provider', default="kimi", choices=["openai", "kimi", "claude", "mock"])
    b1_parser.add_argument('--sink', default="http", choices=["file", "http"], help="观测出口")
    b1_parser.add_argument('--backend', default="http://127.0.0.1:8000", help="后端地址")
    b1_parser.add_argument('--report-dir', default=None, help="输出基目录")
    
    # B2 子命令
    b2_parser = subparsers.add_parser('b2', help='运行批量任务')
    b2_parser.add_argument('--cases', default="cases/cases.jsonl", help='用例文件')
    b2_parser.add_argument('--policy', default="policies/v1.yaml", help='策略文件')
    b2_parser.add_argument('--max-concurrency', type=int, default=4, help='最大并发数')
    
    # 评估子命令
    eval_parser = subparsers.add_parser('eval', help='运行评估')
    eval_parser.add_argument('--runs', required=True, help='运行结果目录')
    eval_parser.add_argument('--cases', default="cases/cases.jsonl", help='用例文件')
    eval_parser.add_argument('--out', default="summary.csv", help='输出文件')
    
    # 服务器子命令
    subparsers.add_parser('server', help='启动后端服务器')
    
    # 测试子命令
    subparsers.add_parser('test', help='运行项目测试')
    
    args = parser.parse_args()
    
    if args.command == 'b1':
        # 设置 B1 参数
        sys.argv = ['b1_cli.py', '--task', args.task, '--policy', args.policy, '--provider', args.provider, '--sink', args.sink, '--backend', args.backend]
        if args.report_dir:
            sys.argv.extend(['--report-dir', args.report_dir])
        run_b1()
    elif args.command == 'b2':
        # 设置 B2 参数
        sys.argv = ['b2_runner.py', '--cases', args.cases, '--policy', args.policy, '--max-concurrency', str(args.max_concurrency)]
        run_b2()
    elif args.command == 'eval':
        # 设置评估参数
        sys.argv = ['b2_eval.py', '--runs', args.runs, '--cases', args.cases, '--out', args.out]
        run_eval()
    elif args.command == 'server':
        run_server()
    elif args.command == 'test':
        return run_test()
    else:
        parser.print_help()
        print("\n快速开始:")
        print("1. 测试项目: python main.py test")
        print("2. 单任务运行: python main.py b1 --task '计算 2+3'")
        print("3. 启动服务器: python main.py server")

if __name__ == "__main__":
    main()
