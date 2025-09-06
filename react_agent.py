"""
ReAct Agent 核心实现
基于 LangChain 框架的 Reasoning + Acting 模式
"""
import re
import time
from typing import Dict, Any, List, Optional
from langchain.schema import HumanMessage, AIMessage
from langchain.agents import initialize_agent, AgentType
from langchain.memory import ConversationBufferMemory
from langchain.prompts import PromptTemplate

from model_config import ModelConfig
from mcp_tools import MCPToolManager
from trace_capture import trace_capture, StepType


class ReActAgent:
    """ReAct 模式的智能代理"""
    
    def __init__(self):
        # 初始化模型
        self.llm = ModelConfig.get_model()
        
        # 初始化工具管理器
        self.tool_manager = MCPToolManager()
        self.tools = self.tool_manager.to_langchain_tools()
        
        # 初始化记忆
        self.memory = ConversationBufferMemory(
            memory_key="chat_history",
            return_messages=True
        )
        
        # ReAct 提示词模板
        self.react_prompt = PromptTemplate(
            input_variables=["input", "tools", "tool_names", "agent_scratchpad"],
            template="""你是一个能够进行推理和行动的智能助手。请按照以下格式进行思考和行动：

可用工具：
{tools}

工具名称：{tool_names}

请使用以下格式：

问题：用户的问题
思考：我需要分析这个问题并决定下一步行动
行动：选择要使用的工具
行动输入：工具的输入参数
观察：工具执行的结果
...（重复思考-行动-观察的循环，直到找到答案）
思考：现在我有了足够的信息来回答问题
最终答案：对用户问题的完整回答

开始！

问题：{input}
{agent_scratchpad}"""
        )
    
    def _parse_thought_action(self, text: str) -> Dict[str, str]:
        """解析思考和行动"""
        result = {}
        
        # 提取思考
        thought_match = re.search(r'思考：(.+?)(?=行动：|最终答案：|$)', text, re.DOTALL)
        if thought_match:
            result['thought'] = thought_match.group(1).strip()
        
        # 提取行动
        action_match = re.search(r'行动：(.+?)(?=行动输入：|$)', text, re.DOTALL)
        if action_match:
            result['action'] = action_match.group(1).strip()
        
        # 提取行动输入
        action_input_match = re.search(r'行动输入：(.+?)(?=观察：|思考：|最终答案：|$)', text, re.DOTALL)
        if action_input_match:
            result['action_input'] = action_input_match.group(1).strip()
        
        # 提取最终答案
        final_answer_match = re.search(r'最终答案：(.+?)$', text, re.DOTALL)
        if final_answer_match:
            result['final_answer'] = final_answer_match.group(1).strip()
        
        return result
    
    def _execute_action(self, action: str, action_input: str) -> str:
        """执行行动并记录轨迹"""
        start_time = time.time()
        
        try:
            # 查找对应的工具
            tool = None
            for t in self.tools:
                if t.name.lower() == action.lower():
                    tool = t
                    break
            
            if not tool:
                return f"错误：未找到工具 '{action}'"
            
            # 执行工具
            result = tool.func(action_input)
            execution_time = time.time() - start_time
            
            # 记录工具调用轨迹
            trace_capture.add_tool_call(
                tool_name=action,
                input_params={"input": action_input},
                output={"result": result},
                execution_time=execution_time,
                success=True
            )
            
            return result
            
        except Exception as e:
            execution_time = time.time() - start_time
            error_msg = f"工具执行错误: {e}"
            
            # 记录失败的工具调用
            trace_capture.add_tool_call(
                tool_name=action,
                input_params={"input": action_input},
                output={"error": error_msg},
                execution_time=execution_time,
                success=False
            )
            
            return error_msg
    
    def run(self, query: str, max_iterations: int = 10) -> str:
        """运行 ReAct 循环"""
        # 开始轨迹记录
        trace_id = trace_capture.start_trace(query)
        
        try:
            # 构建初始提示
            tools_desc = "\n".join([f"- {tool.name}: {tool.description}" for tool in self.tools])
            tool_names = ", ".join([tool.name for tool in self.tools])
            
            agent_scratchpad = ""
            
            for iteration in range(max_iterations):
                # 构建当前提示
                prompt = self.react_prompt.format(
                    input=query,
                    tools=tools_desc,
                    tool_names=tool_names,
                    agent_scratchpad=agent_scratchpad
                )
                
                # 获取模型响应
                start_time = time.time()
                response = self.llm.invoke([HumanMessage(content=prompt)])
                thinking_time = time.time() - start_time
                
                response_text = response.content if hasattr(response, 'content') else str(response)
                
                # 解析响应
                parsed = self._parse_thought_action(response_text)
                
                # 记录思考步骤
                if 'thought' in parsed:
                    trace_capture.add_step(
                        step_type=StepType.THOUGHT,
                        content=parsed['thought'],
                        execution_time=thinking_time,
                        token_count=len(response_text.split()),  # 简单的token估算
                        metadata={"iteration": iteration}
                    )
                
                # 检查是否有最终答案
                if 'final_answer' in parsed:
                    trace_capture.add_step(
                        step_type=StepType.FINAL_ANSWER,
                        content=parsed['final_answer'],
                        metadata={"iteration": iteration}
                    )
                    
                    # 结束轨迹记录
                    trace_capture.end_trace(
                        success=True,
                        final_answer=parsed['final_answer']
                    )
                    
                    return parsed['final_answer']
                
                # 执行行动
                if 'action' in parsed and 'action_input' in parsed:
                    action = parsed['action']
                    action_input = parsed['action_input']
                    
                    # 记录行动步骤
                    trace_capture.add_step(
                        step_type=StepType.ACTION,
                        content=f"工具: {action}, 输入: {action_input}",
                        metadata={
                            "iteration": iteration,
                            "tool_name": action,
                            "tool_input": action_input
                        }
                    )
                    
                    # 执行工具
                    observation = self._execute_action(action, action_input)
                    
                    # 记录观察结果
                    trace_capture.add_step(
                        step_type=StepType.OBSERVATION,
                        content=observation,
                        metadata={"iteration": iteration}
                    )
                    
                    # 更新agent_scratchpad
                    agent_scratchpad += f"\n思考：{parsed.get('thought', '')}\n"
                    agent_scratchpad += f"行动：{action}\n"
                    agent_scratchpad += f"行动输入：{action_input}\n"
                    agent_scratchpad += f"观察：{observation}\n"
                
                else:
                    # 如果没有明确的行动，尝试直接回答
                    final_answer = response_text
                    trace_capture.add_step(
                        step_type=StepType.FINAL_ANSWER,
                        content=final_answer,
                        metadata={"iteration": iteration}
                    )
                    
                    trace_capture.end_trace(
                        success=True,
                        final_answer=final_answer
                    )
                    
                    return final_answer
            
            # 如果达到最大迭代次数
            error_msg = f"达到最大迭代次数 ({max_iterations})，未能完成任务"
            trace_capture.end_trace(
                success=False,
                error_message=error_msg
            )
            
            return error_msg
            
        except Exception as e:
            error_msg = f"执行过程中发生错误: {e}"
            trace_capture.end_trace(
                success=False,
                error_message=error_msg
            )
            
            return error_msg
    
    def get_trace_info(self) -> Dict[str, Any]:
        """获取最近的轨迹信息"""
        if not trace_capture.traces:
            return {"message": "暂无轨迹记录"}
        
        latest_trace = trace_capture.traces[-1]
        return {
            "trace_id": latest_trace.trace_id,
            "query": latest_trace.query,
            "success": latest_trace.success,
            "steps_count": len(latest_trace.steps),
            "tool_calls_count": len(latest_trace.tool_calls),
            "total_tokens": latest_trace.total_tokens,
            "start_time": latest_trace.start_time,
            "end_time": latest_trace.end_time
        }
    
    def get_statistics(self) -> Dict[str, Any]:
        """获取统计信息"""
        return trace_capture.get_statistics()
