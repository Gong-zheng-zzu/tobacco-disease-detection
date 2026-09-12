"""
后处理优化对比测试脚本
测试优化前后的性能差异：
1. 烟青虫召回率
2. 白星病误判率
3. 整体mAP
"""
import os
import sys
from pathlib import Path
from ultralytics import YOLO
from collections import defaultdict
import json

# 添加项目路径
BASE_DIR = Path(__file__).resolve().parent.parent
sys.path.append(str(BASE_DIR / "前后端" / "drf_test002"))

# 类别映射
CLASS_NAMES = {
    0: 'baixingbing',    # 白星病
    1: 'huayebing',      # 花叶病
    2: 'yanqingchong',   # 烟青虫
    3: 'yehuobing',      # 野火病
    4: 'healthy',        # 健康
    5: 'deficiency_k'    # 缺钾
}

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
    """后处理优化逻辑（最小化版本）"""
    filtered = confidences.copy()
    detected = detected_classes.copy()

    # 唯一规则：健康+病害逻辑检查
    if 'healthy' in detected and len(detected) > 1:
        other_confs = [filtered[d] for d in detected if d != 'healthy']
        if other_confs and max(other_confs) > filtered['healthy']:
            detected.remove('healthy')
            del filtered['healthy']

    return detected, filtered


def evaluate_on_test_set(model, dataset_dir, apply_optimization=False):
    """
    在测试集上评估模型
    返回：各类别的TP、FP、FN统计
    """
    from PIL import Image

    stats = defaultdict(lambda: {'tp': 0, 'fp': 0, 'fn': 0, 'total_gt': 0})

    # 遍历测试集目录 - 修正路径结构
    labels_dir = Path(dataset_dir) / 'labels' / 'test'
    images_dir = Path(dataset_dir) / 'images' / 'test'

    if not labels_dir.exists():
        print(f"错误：标签目录不存在 {labels_dir}")
        return stats

    label_files = list(labels_dir.glob('*.txt'))
    print(f"找到 {len(label_files)} 个测试样本")

    for label_file in label_files:
        # 读取真实标签
        stem = label_file.stem
        img_path = images_dir / f"{stem}.jpg"
        if not img_path.exists():
            img_path = images_dir / f"{stem}.png"
        if not img_path.exists():
            continue

        # 解析真实标签
        ground_truth = set()
        with open(label_file, 'r') as f:
            for line in f:
                parts = line.strip().split()
                if parts:
                    cls_id = int(parts[0])
                    if cls_id in CLASS_NAMES:
                        ground_truth.add(CLASS_NAMES[cls_id])

        # 统计真实标签数量
        for cls in ground_truth:
            stats[cls]['total_gt'] += 1

        # 模型推理
        results = model.predict(
            source=str(img_path),
            conf=0.35,
            iou=0.4,
            agnostic_nms=True,
            verbose=False
        )

        detected_classes = set()
        confidences = {}

        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                for box_idx in range(len(r.boxes)):
                    cls_id = int(r.boxes.cls[box_idx])
                    conf = float(r.boxes.conf[box_idx])

                    if cls_id in CLASS_NAMES:
                        class_name = CLASS_NAMES[cls_id]
                        detected_classes.add(class_name)
                        if class_name not in confidences or conf > confidences[class_name]:
                            confidences[class_name] = conf

        # 应用后处理（如果启用）
        if apply_optimization:
            detected_classes, confidences = apply_post_processing(detected_classes, confidences)

        # 计算TP、FP、FN
        for cls in detected_classes:
            if cls in ground_truth:
                stats[cls]['tp'] += 1
            else:
                stats[cls]['fp'] += 1

        for cls in ground_truth:
            if cls not in detected_classes:
                stats[cls]['fn'] += 1

    return stats


def calculate_metrics(stats):
    """计算各类别的精确率、召回率、F1"""
    metrics = {}

    for cls, counts in stats.items():
        tp = counts['tp']
        fp = counts['fp']
        fn = counts['fn']

        precision = tp / (tp + fp) if (tp + fp) > 0 else 0
        recall = tp / (tp + fn) if (tp + fn) > 0 else 0
        f1 = 2 * precision * recall / (precision + recall) if (precision + recall) > 0 else 0

        metrics[cls] = {
            'precision': precision,
            'recall': recall,
            'f1': f1,
            'tp': tp,
            'fp': fp,
            'fn': fn,
            'total_gt': counts['total_gt']
        }

    return metrics


def print_comparison(metrics_before, metrics_after):
    """打印优化前后的对比报告"""
    print("\n" + "="*80)
    print("后处理优化效果对比")
    print("="*80)

    # 检查是否有数据
    if not metrics_before:
        print("错误：无基线数据")
        return
    if not metrics_after:
        print("错误：无优化后数据")
        return

    # 表头
    print(f"{'类别':<12} {'指标':<10} {'优化前':<12} {'优化后':<12} {'变化':<12}")
    print("-"*80)

    for cls in sorted(metrics_before.keys()):
        cn_name = CLASS_TO_CN.get(cls, cls)
        before = metrics_before[cls]
        after = metrics_after.get(cls, before)

        # 召回率对比
        recall_before = before['recall'] * 100
        recall_after = after['recall'] * 100
        recall_diff = recall_after - recall_before
        print(f"{cn_name:<12} {'召回率':<10} {recall_before:>6.2f}%     {recall_after:>6.2f}%     {recall_diff:>+6.2f}%")

        # 精确率对比
        precision_before = before['precision'] * 100
        precision_after = after['precision'] * 100
        precision_diff = precision_after - precision_before
        print(f"{'':12} {'精确率':<10} {precision_before:>6.2f}%     {precision_after:>6.2f}%     {precision_diff:>+6.2f}%")

        # F1对比
        f1_before = before['f1'] * 100
        f1_after = after['f1'] * 100
        f1_diff = f1_after - f1_before
        print(f"{'':12} {'F1':<10} {f1_before:>6.2f}%     {f1_after:>6.2f}%     {f1_diff:>+6.2f}%")
        print("-"*80)

    # 计算整体指标
    print("\n整体指标：")
    total_tp_before = sum(m['tp'] for m in metrics_before.values())
    total_fp_before = sum(m['fp'] for m in metrics_before.values())
    total_fn_before = sum(m['fn'] for m in metrics_before.values())

    total_tp_after = sum(m['tp'] for m in metrics_after.values())
    total_fp_after = sum(m['fp'] for m in metrics_after.values())
    total_fn_after = sum(m['fn'] for m in metrics_after.values())

    if (total_tp_before + total_fp_before) == 0 or (total_tp_before + total_fn_before) == 0:
        print("错误：无有效检测数据")
        return

    overall_precision_before = total_tp_before / (total_tp_before + total_fp_before) * 100
    overall_recall_before = total_tp_before / (total_tp_before + total_fn_before) * 100
    overall_f1_before = 2 * overall_precision_before * overall_recall_before / (overall_precision_before + overall_recall_before)

    overall_precision_after = total_tp_after / (total_tp_after + total_fp_after) * 100
    overall_recall_after = total_tp_after / (total_tp_after + total_fn_after) * 100
    overall_f1_after = 2 * overall_precision_after * overall_recall_after / (overall_precision_after + overall_recall_after)

    print(f"整体精确率: {overall_precision_before:.2f}% → {overall_precision_after:.2f}% ({overall_precision_after - overall_precision_before:+.2f}%)")
    print(f"整体召回率: {overall_recall_before:.2f}% → {overall_recall_after:.2f}% ({overall_recall_after - overall_recall_before:+.2f}%)")
    print(f"整体F1: {overall_f1_before:.2f}% → {overall_f1_after:.2f}% ({overall_f1_after - overall_f1_before:+.2f}%)")


def main():
    # 模型路径
    model_path = BASE_DIR / "前后端" / "drf_test002" / "model_weights" / "yolo_unified_6class_best.pt"
    dataset_dir = BASE_DIR / "unified_tobacco_dataset"

    if not model_path.exists():
        print(f"错误：模型文件不存在 {model_path}")
        return

    print(f"加载模型: {model_path}")
    model = YOLO(str(model_path))

    print("\n[1/2] 评估基线性能（无后处理优化）...")
    stats_before = evaluate_on_test_set(model, dataset_dir, apply_optimization=False)
    metrics_before = calculate_metrics(stats_before)

    print("\n[2/2] 评估优化后性能（启用后处理）...")
    stats_after = evaluate_on_test_set(model, dataset_dir, apply_optimization=True)
    metrics_after = calculate_metrics(stats_after)

    # 打印对比报告
    print_comparison(metrics_before, metrics_after)

    # 保存结果到JSON
    report_path = BASE_DIR / "post_processing_optimization_report.json"
    report = {
        'baseline': {cls: {k: float(v) if isinstance(v, (int, float)) else v
                          for k, v in m.items()}
                    for cls, m in metrics_before.items()},
        'optimized': {cls: {k: float(v) if isinstance(v, (int, float)) else v
                           for k, v in m.items()}
                     for cls, m in metrics_after.items()}
    }

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(report, f, ensure_ascii=False, indent=2)

    print(f"\n详细报告已保存至: {report_path}")


if __name__ == "__main__":
    main()
