# ReAct Agent with LangChain

一个基于 LangChain 框架实现的 ReAct (Reasoning + Acting) 模式智能代理，支持完整的轨迹捕获和可观测性分析。

## 功能特点

- ✅ **完整的 ReAct 循环**: 思考 → 行动 → 观察 → 思考...
- ✅ **MCP 协议工具集成**: 统一的工具调用接口
- ✅ **深度轨迹捕获**: 记录每一步的执行详情
- ✅ **可视化分析**: 多维度的数据展示和分析
- ✅ **多模型支持**: OpenAI、Claude、智谱AI、Kimi API
- ✅ **可观测性**: 性能指标、错误诊断、执行分析

## 快速开始

### 1. 安装依赖

```bash
pip install -r requirements.txt
```

### 2. 配置 API

编辑 `.env` 文件，配置您的 API 密钥：

```env
# 选择模型提供商 (openai/anthropic/zhipu/kimi)
MODEL_PROVIDER=openai
MODEL_NAME=gpt-3.5-turbo

# OpenAI API
OPENAI_API_KEY=your_openai_api_key_here

# Claude API
ANTHROPIC_API_KEY=your_anthropic_api_key_here

# 智谱 AI
ZHIPU_API_KEY=your_zhipu_api_key_here

# Kimi API
KIMI_API_KEY=your_kimi_api_key_here
```

### 3. 运行演示

```bash
# 基础演示
python main.py --mode demo

# 交互模式
python main.py --mode interactive

# 可视化分析
python main.py --mode viz
```

## API 切换说明

通过修改 `.env` 文件中的 `MODEL_PROVIDER` 和 `MODEL_NAME` 来切换不同的 API：

| 提供商 | MODEL_PROVIDER | MODEL_NAME 示例 |
|--------|----------------|-----------------|
| OpenAI | `openai` | `gpt-3.5-turbo`, `gpt-4` |
| Claude | `anthropic` | `claude-3-sonnet-20240229` |
| 智谱AI | `zhipu` | `glm-4` |
| Kimi | `kimi` | `moonshot-v1-8k` |

## 架构设计

```
├── main.py              # 主程序和CLI界面
├── react_agent.py       # ReAct Agent 核心实现
├── model_config.py      # 多模型配置管理
├── mcp_tools.py         # MCP 协议工具集成
├── trace_capture.py     # 轨迹捕获和记录
├── visualization.py     # 可视化分析工具
├── requirements.txt     # 依赖包列表
└── .env                # 环境配置文件
```

## 核心功能

### ReAct 循环

Agent 按照以下模式执行：

1. **思考 (Thought)**: 分析问题，制定策略
2. **行动 (Action)**: 选择并执行工具
3. **观察 (Observation)**: 获取工具执行结果
4. **重复**: 直到找到最终答案

### 可用工具

- **搜索工具**: 网络信息搜索
- **计算器**: 数学表达式计算
- **文件操作**: 文件读写和目录操作

### 轨迹捕获

每次执行都会记录：
- 执行步骤和时间戳
- 工具调用详情
- Token 消耗统计
- 性能指标
- 错误信息和恢复路径

### 可视化分析

- 执行时间线图
- 性能指标对比
- 工具使用分析
- 交互式仪表板
- 数据导出功能

## 使用示例

```python
from react_agent import ReActAgent

# 创建 Agent
agent = ReActAgent()

# 执行查询
result = agent.run("计算 25 * 34 + 128 的结果")
print(result)

# 获取轨迹信息
trace_info = agent.get_trace_info()
print(trace_info)

# 获取统计数据
stats = agent.get_statistics()
print(stats)
```

## 高级功能

### 轨迹分析

```python
from trace_capture import trace_capture
from visualization import visualizer

# 获取所有轨迹
traces = trace_capture.get_all_traces()

# 可视化分析
visualizer.plot_execution_timeline()
visualizer.plot_performance_metrics()
visualizer.analyze_tool_usage()

# 导出报告
visualizer.export_report("analysis_report.json")
```

### 自定义工具

```python
from mcp_tools import MCPTool, MCPToolManager

class CustomTool(MCPTool):
    def __init__(self):
        super().__init__("custom_tool", "自定义工具描述")
    
    def _execute(self, **kwargs):
        # 实现工具逻辑
        return "工具执行结果"

# 注册工具
tool_manager = MCPToolManager()
tool_manager.register_tool(CustomTool())
```

## 注意事项

1. 确保 API 密钥正确配置
2. 网络连接稳定，某些工具需要访问外部服务
3. 可视化功能需要图形界面支持
4. 大量轨迹数据可能影响性能

## 许可证

MIT License
