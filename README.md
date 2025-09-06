
# Kimi-Agent-Minimal (B1/B2)

> 一个 200~500 行的最小 ReAct 执行引擎 + 批量评测与可视化示例（零依赖 Agent 框架，标准库 + matplotlib）。

## 1. 快速开始

```bash
# 单例演示（B1）
python run_demo.py --task "Compute 12*7 and then write to result.txt the sentence 'The result is 84'"

# 批量评测（B2，simple vs deliberate 两个变体做 A/B）
python run_batch.py --cases tests/cases.jsonl --variant simple,deliberate
```

产物位于 `artifacts/`：
- `trace.json`：完整轨迹
- `report.json`：单次运行报告
- `trace.png`：单次轨迹可视化
- `batch_report.json`：批量评测与 A/B 聚合结果

## 2. B1：Agent 执行引擎

- **ReAct 循环**：Thought → Action → Observation，直到 Finish / MaxSteps / Loop 检测
- **工具**：`calculator` / `file_write` / `file_read` / `file_list` / `search(mock)`
- **观测维度**：
  - 轨迹：每步输入、输出、时延、异常、token 估算（len/4）、工具调用数
  - 错误诊断：异常堆栈截断记录；最近 3 步重复同一工具 & 无新增信息 → 视为循环思考
- **可视化**：`src/viz.py` 输出时延条形图

> 引擎核心：`src/engine.py`。不依赖 LangChain/AutoGPT 等框架。

## 3. B2：批量测试与评估

- **并发执行**：`ThreadPoolExecutor`；用例 `jsonl`
- **A/B**：通过 `policy_variant` 切换 `simple`/`deliberate` 策略
- **自动评分**：`expect` 子串命中 + 文件断言（存在/包含）
- **聚合指标**：成功率、平均步数、平均时延、平均 token 估算、平均工具调用数
- **脱敏**：示例正则掩码邮箱/手机号（可扩展）

## 4. 指标与思维质量（建议）

- **有效步率**：产生新 Observation 的步 / 总步
- **聚焦度**：目标关键词漂移率（输入输出 Jaccard 漂移）
- **工具效率**：必要工具数 / 总调用数
- **单位 token 产出**：关键字段命中 / token 估算
- **稳健性**：异常恢复比例、循环思考触发率

## 5. 循环思考与检测

- 硬阈：`max_steps`
- 软判：近 3 步同工具 + Observation 恒等 → `stalled`
- 退出后报告写入 `reason` 便于诊断

## 6. 与真实 LLM/Claude 的集成

- 替换 `SimpleReActPolicy.decide` 为 LLM 调用即可：
  - 将当前轨迹格式化为 ReAct 提示词
  - 解析 LLM 输出中的 Thought/Action/Finish
  - 保留本仓库的**观测/可视化/批量评测**不变
- 可新增 `ClaudePolicy` / `OpenAIChatPolicy`，通过环境变量注入 API Key

## 7. 后续扩展

- 轨迹存储：落地 SQLite/Parquet；加上索引与过滤检索
- 可视化：Flask/Gradio 简易调试台；轨迹对比（高亮差异步）
- 评测：引入更丰富断言（正则、结构、数值误差容忍）
