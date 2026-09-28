"""
快速测试后处理优化效果
在少量样本上验证优化逻辑
"""
import os
import sys
from pathlib import Path

# 添加项目路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "前后端" / "drf_test002"))

# 类别映射
CLASS_TO_CN = {
    'baixingbing': '白星病',
    'huayebing': '花叶病',
    'yanqingchong': '烟青虫',
    'yehuobing': '野火病',
    'healthy': '健康',
    'deficiency_k': '缺钾'
}

# 类别自适应置信度阈值（修正版）
CLASS_CONF_THRESHOLDS = {
    '白星病': 0.36,
    '花叶病': 0.36,
    '烟青虫': 0.25,
    '野火病': 0.35,
    '健康': 0.35,
    '缺钾': 0.35,
}


def apply_post_processing(detected_classes, confidences):
    """后处理优化逻辑"""
    # 步骤1：自适应阈值过滤
    filtered = {}
    for cls_name, conf in confidences.items():
        cn_name = CLASS_TO_CN.get(cls_name, cls_name)
        threshold = CLASS_CONF_THRESHOLDS.get(cn_name, 0.35)
        if conf >= threshold:
            filtered[cls_name] = conf

    detected = set(filtered.keys())

    # 步骤2：白星病-花叶病冲突消歧
    if 'baixingbing' in detected and 'huayebing' in detected:
        conf_diff = abs(filtered['baixingbing'] - filtered['huayebing'])
        if conf_diff < 0.15:
            if filtered['baixingbing'] > filtered['huayebing']:
                detected.remove('huayebing')
                del filtered['huayebing']
            else:
                detected.remove('baixingbing')
                del filtered['baixingbing']

    # 步骤3：健康+病害逻辑检查
    if 'healthy' in detected and len(detected) > 1:
        other_confs = [filtered[d] for d in detected if d != 'healthy']
        if other_confs and max(other_confs) > filtered['healthy']:
            detected.remove('healthy')
            del filtered['healthy']

    return detected, filtered


def test_scenarios():
    """测试典型场景"""
    print("="*80)
    print("后处理优化逻辑测试")
    print("="*80)

    test_cases = [
        {
            "name": "场景1: 烟青虫低置信度 (0.30)",
            "detected": {'yanqingchong'},
            "confidences": {'yanqingchong': 0.30},
            "expected": "保留烟青虫（阈值0.25）"
        },
        {
            "name": "场景2: 烟青虫极低置信度 (0.20)",
            "detected": {'yanqingchong'},
            "confidences": {'yanqingchong': 0.20},
            "expected": "过滤掉烟青虫（低于阈值0.25）"
        },
        {
            "name": "场景3: 白星病-花叶病冲突 (0.42 vs 0.38)",
            "detected": {'baixingbing', 'huayebing'},
            "confidences": {'baixingbing': 0.42, 'huayebing': 0.38},
            "expected": "保留白星病，过滤花叶病（置信度差距<15%）"
        },
        {
            "name": "场景4: 白星病-花叶病明显差异 (0.50 vs 0.32)",
            "detected": {'baixingbing', 'huayebing'},
            "confidences": {'baixingbing': 0.50, 'huayebing': 0.32},
            "expected": "保留白星病，花叶病低于阈值0.40被过滤"
        },
        {
            "name": "场景5: 健康+白星病 (0.40 vs 0.50)",
            "detected": {'healthy', 'baixingbing'},
            "confidences": {'healthy': 0.40, 'baixingbing': 0.50},
            "expected": "保留白星病，过滤健康（病害置信度更高）"
        },
        {
            "name": "场景6: 健康+白星病 (0.50 vs 0.42)",
            "detected": {'healthy', 'baixingbing'},
            "confidences": {'healthy': 0.50, 'baixingbing': 0.42},
            "expected": "保留健康和白星病（健康置信度更高）"
        },
        {
            "name": "场景7: 白星病低置信度 (0.38)",
            "detected": {'baixingbing'},
            "confidences": {'baixingbing': 0.38},
            "expected": "过滤掉白星病（低于阈值0.40）"
        },
    ]

    for i, case in enumerate(test_cases, 1):
        print(f"\n测试 {i}: {case['name']}")
        print(f"  输入检测: {case['detected']}")
        print(f"  置信度: {case['confidences']}")

        # 应用后处理
        result_detected, result_conf = apply_post_processing(
            case['detected'].copy(),
            case['confidences'].copy()
        )

        print(f"  优化后: {result_detected}")
        print(f"  保留置信度: {result_conf}")
        print(f"  预期结果: {case['expected']}")
        print("-"*80)

    print("\n✓ 后处理逻辑测试完成")


def main():
    test_scenarios()


if __name__ == "__main__":
    main()
