"""
Streamlit Web 界面
提供友好的 Web 交互界面
"""
import streamlit as st
import json
import pandas as pd
import plotly.graph_objects as go
from datetime import datetime

from react_agent import ReActAgent
from trace_capture import trace_capture
from visualization import visualizer


def main():
    st.set_page_config(
        page_title="ReAct Agent 分析平台",
        page_icon="🤖",
        layout="wide"
    )
    
    st.title("🤖 ReAct Agent 分析平台")
    st.markdown("基于 LangChain 的智能代理执行和分析平台")
    
    # 侧边栏
    st.sidebar.title("功能导航")
    page = st.sidebar.selectbox(
        "选择功能",
        ["Agent 对话", "轨迹分析", "性能监控", "工具统计"]
    )
    
    if page == "Agent 对话":
        agent_chat_page()
    elif page == "轨迹分析":
        trace_analysis_page()
    elif page == "性能监控":
        performance_monitoring_page()
    elif page == "工具统计":
        tool_statistics_page()


def agent_chat_page():
    st.header("🗣️ Agent 对话")
    
    # 初始化 Agent
    if 'agent' not in st.session_state:
        st.session_state.agent = ReActAgent()
    
    # 对话历史
    if 'chat_history' not in st.session_state:
        st.session_state.chat_history = []
    
    # 输入框
    user_input = st.text_input("请输入您的问题:", key="user_input")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        if st.button("发送", type="primary"):
            if user_input:
                process_user_input(user_input)
    
    with col2:
        if st.button("清空历史"):
            st.session_state.chat_history = []
            st.rerun()
    
    # 显示对话历史
    if st.session_state.chat_history:
        st.subheader("对话历史")
        for i, (question, answer, trace_info) in enumerate(st.session_state.chat_history):
            with st.expander(f"对话 {i+1}: {question[:50]}..."):
                st.write("**问题:**", question)
                st.write("**回答:**", answer)
                
                col1, col2 = st.columns(2)
                with col1:
                    st.write("**执行信息:**")
                    st.json(trace_info)
                
                with col2:
                    if trace_info.get('trace_id'):
                        if st.button(f"查看轨迹详情", key=f"trace_{i}"):
                            show_trace_details(trace_info['trace_id'])


def process_user_input(user_input):
    """处理用户输入"""
    with st.spinner("Agent 正在思考..."):
        result = st.session_state.agent.run(user_input)
        trace_info = st.session_state.agent.get_trace_info()
        
        st.session_state.chat_history.append((user_input, result, trace_info))
    
    st.rerun()


def show_trace_details(trace_id):
    """显示轨迹详情"""
    trace = trace_capture.get_trace(trace_id)
    if trace:
        st.subheader(f"轨迹详情: {trace_id[:8]}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.write("**基本信息:**")
            st.write(f"- 查询: {trace.query}")
            st.write(f"- 状态: {'成功' if trace.success else '失败'}")
            st.write(f"- 开始时间: {trace.start_time}")
            st.write(f"- 结束时间: {trace.end_time}")
        
        with col2:
            st.write("**统计信息:**")
            st.write(f"- 步骤数: {len(trace.steps)}")
            st.write(f"- 工具调用: {len(trace.tool_calls)}")
            st.write(f"- Token 消耗: {trace.total_tokens}")
            st.write(f"- API 调用: {trace.total_api_calls}")
        
        st.subheader("执行步骤")
        for i, step in enumerate(trace.steps):
            with st.expander(f"步骤 {i+1}: {step.step_type.value}"):
                st.write(f"**内容:** {step.content}")
                st.write(f"**时间:** {step.timestamp}")
                st.write(f"**执行时间:** {step.execution_time:.3f}秒")
                if step.metadata:
                    st.write("**元数据:**")
                    st.json(step.metadata)


def trace_analysis_page():
    st.header("📊 轨迹分析")
    
    # 刷新数据
    visualizer.refresh_data()
    traces = trace_capture.get_all_traces()
    
    if not traces:
        st.warning("暂无轨迹数据，请先在对话页面进行一些对话。")
        return
    
    # 轨迹列表
    st.subheader("轨迹列表")
    trace_data = []
    for trace in traces:
        trace_data.append({
            "轨迹ID": trace.trace_id[:8],
            "查询": trace.query[:50] + "..." if len(trace.query) > 50 else trace.query,
            "状态": "成功" if trace.success else "失败",
            "步骤数": len(trace.steps),
            "工具调用": len(trace.tool_calls),
            "Token": trace.total_tokens,
            "开始时间": trace.start_time
        })
    
    df = pd.DataFrame(trace_data)
    st.dataframe(df, use_container_width=True)
    
    # 时间线图
    st.subheader("执行时间线")
    if st.button("生成时间线图"):
        fig = create_timeline_chart(traces[-10:])  # 显示最近10条
        st.plotly_chart(fig, use_container_width=True)


def create_timeline_chart(traces):
    """创建时间线图表"""
    fig = go.Figure()
    
    for i, trace in enumerate(traces):
        if not trace.steps:
            continue
        
        for step in trace.steps:
            step_time = datetime.fromisoformat(step.timestamp)
            
            color_map = {
                "thought": "blue",
                "action": "green", 
                "observation": "orange",
                "final_answer": "red"
            }
            
            color = color_map.get(step.step_type.value, "gray")
            
            fig.add_trace(go.Scatter(
                x=[step_time],
                y=[i],
                mode='markers',
                marker=dict(size=10, color=color),
                name=step.step_type.value,
                text=step.content[:100],
                hovertemplate=f'<b>{step.step_type.value}</b><br>%{{text}}<br>%{{x}}<extra></extra>',
                showlegend=i == 0  # 只在第一条轨迹显示图例
            ))
    
    fig.update_layout(
        title="轨迹执行时间线",
        xaxis_title="时间",
        yaxis_title="轨迹",
        hovermode="closest"
    )
    
    return fig


def performance_monitoring_page():
    st.header("⚡ 性能监控")
    
    stats = trace_capture.get_statistics()
    
    if stats.get("total_traces", 0) == 0:
        st.warning("暂无性能数据")
        return
    
    # 关键指标
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("总轨迹数", stats["total_traces"])
    
    with col2:
        st.metric("成功率", f"{stats['success_rate']:.1%}")
    
    with col3:
        st.metric("平均Token", f"{stats['avg_tokens_per_trace']:.0f}")
    
    with col4:
        st.metric("平均执行时间", f"{stats['avg_execution_time']:.2f}秒")
    
    # 详细统计
    st.subheader("详细统计")
    stats_df = pd.DataFrame([
        {"指标": "总轨迹数", "值": stats["total_traces"]},
        {"指标": "成功轨迹数", "值": stats["successful_traces"]},
        {"指标": "成功率", "值": f"{stats['success_rate']:.2%}"},
        {"指标": "总Token消耗", "值": stats["total_tokens"]},
        {"指标": "平均Token/轨迹", "值": f"{stats['avg_tokens_per_trace']:.1f}"},
        {"指标": "总API调用", "值": stats["total_api_calls"]},
        {"指标": "平均API调用/轨迹", "值": f"{stats['avg_api_calls_per_trace']:.1f}"},
        {"指标": "平均执行时间", "值": f"{stats['avg_execution_time']:.2f}秒"}
    ])
    
    st.dataframe(stats_df, use_container_width=True)


def tool_statistics_page():
    st.header("🔧 工具统计")
    
    visualizer.refresh_data()
    tool_stats = visualizer.analyze_tool_usage()
    
    if not tool_stats:
        st.warning("暂无工具使用数据")
        return
    
    # 工具使用概览
    st.subheader("工具使用概览")
    
    tool_data = []
    for tool_name, stats in tool_stats.items():
        tool_data.append({
            "工具名称": tool_name,
            "使用次数": stats["count"],
            "成功次数": stats["success_count"],
            "成功率": f"{stats['success_rate']:.1%}",
            "平均执行时间": f"{stats['avg_time']:.3f}秒",
            "总执行时间": f"{stats['total_time']:.3f}秒"
        })
    
    df = pd.DataFrame(tool_data)
    st.dataframe(df, use_container_width=True)
    
    # 可视化图表
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("使用频率")
        fig_freq = go.Figure(data=[
            go.Bar(
                x=list(tool_stats.keys()),
                y=[stats["count"] for stats in tool_stats.values()]
            )
        ])
        fig_freq.update_layout(title="工具使用频率")
        st.plotly_chart(fig_freq, use_container_width=True)
    
    with col2:
        st.subheader("成功率")
        fig_success = go.Figure(data=[
            go.Bar(
                x=list(tool_stats.keys()),
                y=[stats["success_rate"] for stats in tool_stats.values()]
            )
        ])
        fig_success.update_layout(title="工具成功率", yaxis=dict(range=[0, 1]))
        st.plotly_chart(fig_success, use_container_width=True)


if __name__ == "__main__":
    main()
