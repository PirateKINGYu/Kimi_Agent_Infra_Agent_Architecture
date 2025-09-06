# -*- coding: utf-8 -*-
"""深度轨迹分析工具：Agent 行为模式识别和质量评估"""
from __future__ import annotations
import json
import statistics
from typing import Dict, List, Any, Tuple
from dataclasses import dataclass
from .trace import RunTrace, TraceStep


@dataclass
class ThinkingPattern:
    """思维模式分析结果"""
    depth_score: float  # 思考深度评分 (0-1)
    coherence_score: float  # 逻辑连贯性评分 (0-1)
    efficiency_score: float  # 效率评分 (0-1)
    loop_detected: bool  # 是否检测到循环思考
    decision_quality: float  # 决策质量评分 (0-1)


@dataclass
class PerformanceMetrics:
    """性能指标"""
    total_tokens: int
    avg_latency: float
    token_efficiency: float  # tokens per second
    step_count: int
    success_rate: float
    error_count: int


@dataclass
class BehaviorAnalysis:
    """行为分析结果"""
    tool_usage_pattern: Dict[str, int]
    strategy_changes: List[int]  # 策略改变的步骤
    retry_patterns: List[Tuple[int, str]]  # 重试模式
    exploration_vs_exploitation: float  # 探索vs利用比例


class TraceAnalyzer:
    """轨迹分析器：深度分析 Agent 执行过程"""
    
    def __init__(self):
        self.thinking_keywords = {
            'planning': ['计划', '规划', '步骤', '流程', 'plan', 'step'],
            'reasoning': ['因为', '所以', '推理', 'because', 'therefore', 'reason'],
            'evaluation': ['评估', '检查', '验证', 'evaluate', 'check', 'verify'],
            'reflection': ['反思', '总结', '回顾', 'reflect', 'summary', 'review']
        }
    
    def analyze_run(self, run: RunTrace) -> Dict[str, Any]:
        """全面分析一次运行"""
        steps = run.steps
        
        return {
            'thinking_pattern': self._analyze_thinking_pattern(steps),
            'performance_metrics': self._calculate_performance_metrics(steps),
            'behavior_analysis': self._analyze_behavior(steps),
            'quality_assessment': self._assess_quality(steps, run.final_answer),
            'anomaly_detection': self._detect_anomalies(steps),
            'improvement_suggestions': self._generate_suggestions(steps)
        }
    
    def _analyze_thinking_pattern(self, steps: List[TraceStep]) -> ThinkingPattern:
        """分析思维模式"""
        thoughts = [step.thought for step in steps if step.thought]
        
        # 计算思考深度：基于思考长度和复杂度
        depth_scores = []
        for thought in thoughts:
            length_score = min(len(thought) / 200, 1.0)  # 长度得分
            complexity_score = self._calculate_complexity(thought)
            depth_scores.append((length_score + complexity_score) / 2)
        
        depth_score = statistics.mean(depth_scores) if depth_scores else 0
        
        # 计算连贯性：检查前后思考的关联性
        coherence_score = self._calculate_coherence(thoughts)
        
        # 计算效率：思考与行动的比例
        action_count = len([s for s in steps if s.action])
        thought_count = len(thoughts)
        efficiency_score = action_count / max(thought_count, 1)
        
        # 检测循环思考
        loop_detected = self._detect_thinking_loops(thoughts)
        
        # 决策质量：基于错误率和行动成功率
        error_rate = len([s for s in steps if s.error]) / max(len(steps), 1)
        decision_quality = 1 - error_rate
        
        return ThinkingPattern(
            depth_score=depth_score,
            coherence_score=coherence_score,
            efficiency_score=efficiency_score,
            loop_detected=loop_detected,
            decision_quality=decision_quality
        )
    
    def _calculate_complexity(self, thought: str) -> float:
        """计算思考复杂度"""
        if not thought:
            return 0
        
        # 基于关键词密度
        total_keywords = 0
        for category, keywords in self.thinking_keywords.items():
            for keyword in keywords:
                total_keywords += thought.lower().count(keyword)
        
        complexity = min(total_keywords / len(thought.split()), 1.0)
        return complexity
    
    def _calculate_coherence(self, thoughts: List[str]) -> float:
        """计算思考连贯性"""
        if len(thoughts) < 2:
            return 1.0
        
        coherence_scores = []
        for i in range(1, len(thoughts)):
            prev_thought = thoughts[i-1].lower()
            curr_thought = thoughts[i].lower()
            
            # 简单的词汇重叠度计算
            prev_words = set(prev_thought.split())
            curr_words = set(curr_thought.split())
            
            if len(prev_words) == 0 or len(curr_words) == 0:
                coherence_scores.append(0)
            else:
                overlap = len(prev_words.intersection(curr_words))
                total = len(prev_words.union(curr_words))
                coherence_scores.append(overlap / total)
        
        return statistics.mean(coherence_scores)
    
    def _detect_thinking_loops(self, thoughts: List[str]) -> bool:
        """检测循环思考"""
        if len(thoughts) < 3:
            return False
        
        # 检查相似的思考模式
        for i in range(len(thoughts) - 2):
            for j in range(i + 2, len(thoughts)):
                similarity = self._calculate_similarity(thoughts[i], thoughts[j])
                if similarity > 0.8:  # 高相似度阈值
                    return True
        
        return False
    
    def _calculate_similarity(self, text1: str, text2: str) -> float:
        """计算文本相似度"""
        words1 = set(text1.lower().split())
        words2 = set(text2.lower().split())
        
        if len(words1) == 0 and len(words2) == 0:
            return 1.0
        if len(words1) == 0 or len(words2) == 0:
            return 0.0
        
        intersection = words1.intersection(words2)
        union = words1.union(words2)
        
        return len(intersection) / len(union)
    
    def _calculate_performance_metrics(self, steps: List[TraceStep]) -> PerformanceMetrics:
        """计算性能指标"""
        total_tokens = sum(step.model_usage.get('total_tokens', 0) for step in steps)
        
        latencies = [step.latency_s for step in steps if step.latency_s > 0]
        avg_latency = statistics.mean(latencies) if latencies else 0
        
        total_time = sum(latencies)
        token_efficiency = total_tokens / total_time if total_time > 0 else 0
        
        error_count = len([s for s in steps if s.error])
        success_rate = 1 - (error_count / max(len(steps), 1))
        
        return PerformanceMetrics(
            total_tokens=total_tokens,
            avg_latency=avg_latency,
            token_efficiency=token_efficiency,
            step_count=len(steps),
            success_rate=success_rate,
            error_count=error_count
        )
    
    def _analyze_behavior(self, steps: List[TraceStep]) -> BehaviorAnalysis:
        """分析行为模式"""
        # 工具使用模式
        tool_usage = {}
        for step in steps:
            if step.action:
                tool_usage[step.action] = tool_usage.get(step.action, 0) + 1
        
        # 策略改变检测
        strategy_changes = []
        prev_tool = None
        for i, step in enumerate(steps):
            if step.action and step.action != prev_tool:
                if prev_tool is not None:
                    strategy_changes.append(i)
                prev_tool = step.action
        
        # 重试模式检测
        retry_patterns = []
        for i in range(1, len(steps)):
            if steps[i].action == steps[i-1].action and steps[i-1].error:
                retry_patterns.append((i, steps[i].action))
        
        # 探索vs利用比例
        unique_tools = len(set(s.action for s in steps if s.action))
        total_actions = len([s for s in steps if s.action])
        exploration_ratio = unique_tools / max(total_actions, 1)
        
        return BehaviorAnalysis(
            tool_usage_pattern=tool_usage,
            strategy_changes=strategy_changes,
            retry_patterns=retry_patterns,
            exploration_vs_exploitation=exploration_ratio
        )
    
    def _assess_quality(self, steps: List[TraceStep], final_answer: str) -> Dict[str, float]:
        """评估整体质量"""
        # 完成度评估
        completion_score = 1.0 if final_answer and len(final_answer) > 10 else 0.5
        
        # 效率评估：步骤数与任务复杂度的比例
        efficiency_score = min(1.0, 5.0 / max(len(steps), 1))
        
        # 稳定性评估：错误率
        error_rate = len([s for s in steps if s.error]) / max(len(steps), 1)
        stability_score = 1 - error_rate
        
        # 综合评分
        overall_score = (completion_score + efficiency_score + stability_score) / 3
        
        return {
            'completion': completion_score,
            'efficiency': efficiency_score,
            'stability': stability_score,
            'overall': overall_score
        }
    
    def _detect_anomalies(self, steps: List[TraceStep]) -> List[Dict[str, Any]]:
        """检测异常模式"""
        anomalies = []
        
        # 检测异常长的思考时间
        latencies = [s.latency_s for s in steps if s.latency_s > 0]
        if latencies:
            avg_latency = statistics.mean(latencies)
            threshold = avg_latency * 3
            
            for i, step in enumerate(steps):
                if step.latency_s > threshold:
                    anomalies.append({
                        'type': 'high_latency',
                        'step': i + 1,
                        'value': step.latency_s,
                        'description': f'响应时间异常：{step.latency_s:.2f}s (平均: {avg_latency:.2f}s)'
                    })
        
        # 检测重复错误
        error_patterns = {}
        for i, step in enumerate(steps):
            if step.error:
                error_type = step.error.split(':')[0]
                if error_type in error_patterns:
                    error_patterns[error_type].append(i + 1)
                else:
                    error_patterns[error_type] = [i + 1]
        
        for error_type, step_numbers in error_patterns.items():
            if len(step_numbers) >= 2:
                anomalies.append({
                    'type': 'repeated_error',
                    'steps': step_numbers,
                    'description': f'重复错误 "{error_type}" 在步骤 {step_numbers} 中出现'
                })
        
        return anomalies
    
    def _generate_suggestions(self, steps: List[TraceStep]) -> List[str]:
        """生成改进建议"""
        suggestions = []
        
        # 基于错误率的建议
        error_rate = len([s for s in steps if s.error]) / max(len(steps), 1)
        if error_rate > 0.3:
            suggestions.append("错误率较高，建议增强输入验证和错误处理机制")
        
        # 基于效率的建议
        if len(steps) > 10:
            suggestions.append("执行步骤较多，考虑优化任务分解策略")
        
        # 基于工具使用的建议
        tool_usage = {}
        for step in steps:
            if step.action:
                tool_usage[step.action] = tool_usage.get(step.action, 0) + 1
        
        if len(tool_usage) == 1:
            suggestions.append("工具使用单一，考虑扩展工具集以提高灵活性")
        
        # 基于思考质量的建议
        avg_thought_length = statistics.mean([len(s.thought or '') for s in steps])
        if avg_thought_length < 20:
            suggestions.append("思考深度不足，建议增强推理过程的详细程度")
        
        return suggestions


# 使用示例函数
def analyze_agent_quality(run_data: Dict) -> Dict[str, Any]:
    """分析 Agent 运行质量的便捷函数"""
    analyzer = TraceAnalyzer()
    
    # 构造 RunTrace 对象
    run = RunTrace(
        task=run_data['run']['task'],
        run_dir='',
        start_time=0,
        run_id=run_data['run']['run_id']
    )
    run.final_answer = run_data['run']['final_answer']
    
    # 构造 TraceStep 对象
    steps = []
    for step_data in run_data['steps']:
        step = TraceStep(
            step=step_data['step_no'],
            thought=step_data['thought'],
            action=step_data['action'],
            action_input=step_data['action_input'],
            observation=step_data['observation'],
            error=step_data['error'],
            latency_s=step_data['latency_s'],
            model_usage=json.loads(step_data['model_usage_json'] or '{}')
        )
        steps.append(step)
    
    run.steps = steps
    
    return analyzer.analyze_run(run)
