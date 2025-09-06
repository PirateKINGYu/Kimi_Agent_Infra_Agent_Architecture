"""
可视化分析工具
提供轨迹数据的可视化展示和分析功能
"""
import json
import pandas as pd
import matplotlib.pyplot as plt
import plotly.graph_objects as go
import plotly.express as px
from typing import List, Dict, Any
from datetime import datetime

from trace_capture import trace_capture, ExecutionTrace, StepType

# 设置中文字体
plt.rcParams['font.sans-serif'] = ['SimHei']
plt.rcParams['axes.unicode_minus'] = False


class TraceVisualizer:
    """轨迹可视化工具"""
    
    def __init__(self):
        self.traces = trace_capture.get_all_traces()
    
    def refresh_data(self):
        """刷新数据"""
        self.traces = trace_capture.get_all_traces()
    
    def plot_execution_timeline(self, trace_id: str = None):
        """绘制执行时间线"""
        if trace_id:
            traces_to_plot = [trace_capture.get_trace(trace_id)]
            if not traces_to_plot[0]:
                print(f"轨迹 {trace_id} 不存在")
                return
        else:
            traces_to_plot = self.traces[-5:]  # 显示最近5条轨迹
        
        fig, ax = plt.subplots(figsize=(12, 8))
        
        for i, trace in enumerate(traces_to_plot):
            if not trace.steps:
                continue
            
            # 为每个步骤创建时间点
            times = []
            labels = []
            colors = []
            
            for step in trace.steps:
                step_time = datetime.fromisoformat(step.timestamp)
                times.append(step_time)
                labels.append(f"{step.step_type.value}: {step.content[:30]}...")
                
                # 根据步骤类型设置颜色
                if step.step_type == StepType.THOUGHT:
                    colors.append('blue')
                elif step.step_type == StepType.ACTION:
                    colors.append('green')
                elif step.step_type == StepType.OBSERVATION:
                    colors.append('orange')
                else:
                    colors.append('red')
            
            # 绘制时间线
            y_pos = [i] * len(times)
            ax.scatter(times, y_pos, c=colors, s=100, alpha=0.7)
            
            # 添加连接线
            if len(times) > 1:
                ax.plot(times, y_pos, 'k-', alpha=0.3, linewidth=1)
        
        ax.set_yticks(range(len(traces_to_plot)))
        ax.set_yticklabels([f"轨迹 {i+1}" for i in range(len(traces_to_plot))])
        ax.set_xlabel("时间")
        ax.set_title("执行时间线")
        
        # 添加图例
        legend_elements = [
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='blue', label='思考'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='green', label='行动'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='orange', label='观察'),
            plt.Line2D([0], [0], marker='o', color='w', markerfacecolor='red', label='最终答案')
        ]
        ax.legend(handles=legend_elements)
        
        plt.xticks(rotation=45)
        plt.tight_layout()
        plt.show()
    
    def plot_performance_metrics(self):
        """绘制性能指标"""
        if not self.traces:
            print("没有轨迹数据")
            return
        
        # 提取数据
        data = {
            'trace_id': [],
            'execution_time': [],
            'token_count': [],
            'api_calls': [],
            'steps_count': [],
            'success': []
        }
        
        for trace in self.traces:
            data['trace_id'].append(trace.trace_id[:8])  # 只显示前8位
            
            # 计算执行时间
            if trace.start_time and trace.end_time:
                start = datetime.fromisoformat(trace.start_time)
                end = datetime.fromisoformat(trace.end_time)
                exec_time = (end - start).total_seconds()
            else:
                exec_time = 0
            
            data['execution_time'].append(exec_time)
            data['token_count'].append(trace.total_tokens)
            data['api_calls'].append(trace.total_api_calls)
            data['steps_count'].append(len(trace.steps))
            data['success'].append(trace.success)
        
        # 创建子图
        fig, axes = plt.subplots(2, 2, figsize=(15, 10))
        
        # 执行时间
        axes[0, 0].bar(data['trace_id'], data['execution_time'])
        axes[0, 0].set_title('执行时间 (秒)')
        axes[0, 0].set_ylabel('时间 (秒)')
        
        # Token 消耗
        axes[0, 1].bar(data['trace_id'], data['token_count'])
        axes[0, 1].set_title('Token 消耗')
        axes[0, 1].set_ylabel('Token 数量')
        
        # API 调用次数
        axes[1, 0].bar(data['trace_id'], data['api_calls'])
        axes[1, 0].set_title('API 调用次数')
        axes[1, 0].set_ylabel('调用次数')
        
        # 步骤数量
        axes[1, 1].bar(data['trace_id'], data['steps_count'])
        axes[1, 1].set_title('执行步骤数量')
        axes[1, 1].set_ylabel('步骤数')
        
        # 旋转x轴标签
        for ax in axes.flat:
            ax.tick_params(axis='x', rotation=45)
        
        plt.tight_layout()
        plt.show()
    
    def create_interactive_dashboard(self):
        """创建交互式仪表板"""
        if not self.traces:
            print("没有轨迹数据")
            return
        
        # 准备数据
        df_traces = []
        for trace in self.traces:
            if trace.start_time and trace.end_time:
                start = datetime.fromisoformat(trace.start_time)
                end = datetime.fromisoformat(trace.end_time)
                exec_time = (end - start).total_seconds()
            else:
                exec_time = 0
            
            df_traces.append({
                'trace_id': trace.trace_id[:8],
                'query': trace.query[:50] + "..." if len(trace.query) > 50 else trace.query,
                'execution_time': exec_time,
                'tokens': trace.total_tokens,
                'api_calls': trace.total_api_calls,
                'steps': len(trace.steps),
                'success': '成功' if trace.success else '失败'
            })
        
        df = pd.DataFrame(df_traces)
        
        # 创建交互式图表
        fig = go.Figure()
        
        # 添加散点图：执行时间 vs Token消耗
        fig.add_trace(go.Scatter(
            x=df['execution_time'],
            y=df['tokens'],
            mode='markers',
            marker=dict(
                size=df['steps'] * 3,  # 根据步骤数调整点的大小
                color=df['api_calls'],
                colorscale='Viridis',
                showscale=True,
                colorbar=dict(title="API调用次数")
            ),
            text=df['query'],
            hovertemplate='<b>查询:</b> %{text}<br>' +
                          '<b>执行时间:</b> %{x:.2f}秒<br>' +
                          '<b>Token:</b> %{y}<br>' +
                          '<b>步骤数:</b> %{marker.size}<extra></extra>',
            name='轨迹'
        ))
        
        fig.update_layout(
            title='轨迹性能分析 (气泡大小=步骤数, 颜色=API调用次数)',
            xaxis_title='执行时间 (秒)',
            yaxis_title='Token 消耗',
            hovermode='closest'
        )
        
        fig.show()
    
    def analyze_tool_usage(self):
        """分析工具使用情况"""
        tool_stats = {}
        
        for trace in self.traces:
            for tool_call in trace.tool_calls:
                tool_name = tool_call.tool_name
                if tool_name not in tool_stats:
                    tool_stats[tool_name] = {
                        'count': 0,
                        'success_count': 0,
                        'total_time': 0.0,
                        'avg_time': 0.0
                    }
                
                tool_stats[tool_name]['count'] += 1
                if tool_call.success:
                    tool_stats[tool_name]['success_count'] += 1
                tool_stats[tool_name]['total_time'] += tool_call.execution_time
        
        # 计算平均时间
        for tool_name in tool_stats:
            stats = tool_stats[tool_name]
            if stats['count'] > 0:
                stats['avg_time'] = stats['total_time'] / stats['count']
                stats['success_rate'] = stats['success_count'] / stats['count']
        
        # 可视化
        if tool_stats:
            tools = list(tool_stats.keys())
            counts = [tool_stats[tool]['count'] for tool in tools]
            success_rates = [tool_stats[tool]['success_rate'] for tool in tools]
            
            fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 6))
            
            # 工具使用频率
            ax1.bar(tools, counts)
            ax1.set_title('工具使用频率')
            ax1.set_ylabel('使用次数')
            ax1.tick_params(axis='x', rotation=45)
            
            # 工具成功率
            ax2.bar(tools, success_rates)
            ax2.set_title('工具成功率')
            ax2.set_ylabel('成功率')
            ax2.set_ylim(0, 1)
            ax2.tick_params(axis='x', rotation=45)
            
            plt.tight_layout()
            plt.show()
            
            return tool_stats
        else:
            print("没有工具使用数据")
            return {}
    
    def export_report(self, filename: str = "trace_report.json"):
        """导出分析报告"""
        report = {
            "generated_at": datetime.now().isoformat(),
            "summary": trace_capture.get_statistics(),
            "tool_usage": self.analyze_tool_usage(),
            "traces": []
        }
        
        for trace in self.traces:
            trace_data = {
                "trace_id": trace.trace_id,
                "query": trace.query,
                "success": trace.success,
                "start_time": trace.start_time,
                "end_time": trace.end_time,
                "steps_count": len(trace.steps),
                "tool_calls_count": len(trace.tool_calls),
                "total_tokens": trace.total_tokens
            }
            report["traces"].append(trace_data)
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(report, f, ensure_ascii=False, indent=2)
        
        print(f"报告已导出到: {filename}")


# 全局可视化工具实例
visualizer = TraceVisualizer()
