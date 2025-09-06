# -*- coding: utf-8 -*-
"""测试深度分析功能"""
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..', 'src'))

from core.analysis import analyze_agent_quality

# 创建测试数据
test_data = {
    'run': {
        'run_id': 'test_001',
        'task': '测试任务：计算 1+1',
        'final_answer': '1+1=2'
    },
    'steps': [
        {
            'step_no': 1,
            'thought': '我需要计算 1+1 的结果',
            'action': 'calculate',
            'action_input': '1+1',
            'observation': '计算结果为 2',
            'error': None,
            'latency_s': 0.5,
            'model_usage_json': '{"total_tokens": 50, "prompt_tokens": 30, "completion_tokens": 20}'
        },
        {
            'step_no': 2,
            'thought': '计算完成，我得到了正确的答案',
            'action': 'finalize',
            'action_input': '2',
            'observation': '任务完成',
            'error': None,
            'latency_s': 0.3,
            'model_usage_json': '{"total_tokens": 40, "prompt_tokens": 25, "completion_tokens": 15}'
        }
    ]
}

if __name__ == "__main__":
    print("开始测试深度分析功能...")
    
    try:
        result = analyze_agent_quality(test_data)
        print("✅ 分析完成！")
        print("\n=== 分析结果 ===")
        
        # 思维模式
        pattern = result['thinking_pattern']
        print(f"思考深度: {pattern.depth_score:.2f}")
        print(f"逻辑连贯性: {pattern.coherence_score:.2f}")
        print(f"执行效率: {pattern.efficiency_score:.2f}")
        print(f"决策质量: {pattern.decision_quality:.2f}")
        
        # 性能指标
        perf = result['performance_metrics']
        print(f"\n总Token数: {perf.total_tokens}")
        print(f"平均延迟: {perf.avg_latency:.3f}s")
        print(f"成功率: {perf.success_rate:.2f}")
        
        # 质量评估
        quality = result['quality_assessment']
        print(f"\n综合评分: {quality['overall']:.2f}")
        
        print("\n✅ 深度分析功能测试通过！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()
