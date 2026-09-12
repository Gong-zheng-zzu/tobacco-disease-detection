"""
模型性能对比测试脚本
对比优化前后的模型性能，生成详细报告
"""
import os
import json
import time
from pathlib import Path
from ultralytics import YOLO
from PIL import Image
import numpy as np

# 测试集路径
BASE_DIR = Path(__file__).parent.parent
TEST_IMAGES_DIR = BASE_DIR / "unified_tobacco_dataset" / "images" / "test"
TEST_LABELS_DIR = BASE_DIR / "unified_tobacco_dataset" / "labels" / "test"

CLASS_NAMES = {
    0: '白星病',
    1: '花叶病',
    2: '烟青虫',
    3: '野火病',
    4: '健康',
    5: '缺钾'
}

def load_model(model_path):
    """加载模型"""
    if not os.path.exists(model_path):
        print(f"模型不存在: {model_path}")
        return None
    return YOLO(model_path)

def test_model_performance(model, test_images, name="Model"):
    """测试模型性能"""
    print(f"\n{'=' * 60}")
    print(f"测试模型: {name}")
    print(f"{'=' * 60}")

    total_time = 0
    results_list = []

    for img_path in test_images[:50]:  # 测试前50张
        img = Image.open(img_path).convert('RGB')

        start = time.time()
        results = model.predict(
            source=img,
            conf=0.35,
            iou=0.4,
            agnostic_nms=True,
            verbose=False
        )
        inference_time = (time.time() - start) * 1000  # ms
        total_time += inference_time

        # 收集检测结果
        detected = []
        for r in results:
            if r.boxes is not None:
                for box in r.boxes:
                    cls_id = int(box.cls[0])
                    conf = float(box.conf[0])
                    detected.append({
                        'class': CLASS_NAMES.get(cls_id, 'unknown'),
                        'confidence': conf
                    })

        results_list.append({
            'image': img_path.name,
            'detections': detected,
            'inference_time_ms': inference_time
        })

    avg_time = total_time / len(results_list)

    print(f"平均推理时间: {avg_time:.2f}ms")
    print(f"FPS: {1000/avg_time:.2f}")

    return {
        'model_name': name,
        'avg_inference_time_ms': avg_time,
        'fps': 1000 / avg_time,
        'total_images_tested': len(results_list),
        'results': results_list
    }

def compare_confusion_reduction(original_results, optimized_results):
    """对比白星病-花叶病混淆改善情况"""
    print(f"\n{'=' * 60}")
    print("白星病-花叶病混淆对比分析")
    print(f"{'=' * 60}")

    # 统计包含白星病或花叶病的检测
    def count_disease_detections(results):
        baixing_count = 0
        huaye_count = 0
        both_count = 0

        for r in results['results']:
            has_baixing = any(d['class'] == '白星病' for d in r['detections'])
            has_huaye = any(d['class'] == '花叶病' for d in r['detections'])

            if has_baixing:
                baixing_count += 1
            if has_huaye:
                huaye_count += 1
            if has_baixing and has_huaye:
                both_count += 1

        return baixing_count, huaye_count, both_count

    orig_b, orig_h, orig_both = count_disease_detections(original_results)
    opt_b, opt_h, opt_both = count_disease_detections(optimized_results)

    print(f"\n原始模型:")
    print(f"  白星病检测: {orig_b}次")
    print(f"  花叶病检测: {orig_h}次")
    print(f"  同时检测: {orig_both}次")

    print(f"\n优化模型:")
    print(f"  白星病检测: {opt_b}次")
    print(f"  花叶病检测: {opt_h}次")
    print(f"  同时检测: {opt_both}次")

    if orig_both > 0:
        reduction = ((orig_both - opt_both) / orig_both) * 100
        print(f"\n混淆减少: {reduction:.1f}%")

def generate_comparison_report(results_dict, output_file="model_comparison_report.json"):
    """生成对比报告"""
    report_path = BASE_DIR / output_file

    with open(report_path, 'w', encoding='utf-8') as f:
        json.dump(results_dict, f, ensure_ascii=False, indent=2)

    print(f"\n对比报告已保存: {report_path}")

    # 打印摘要
    print(f"\n{'=' * 60}")
    print("性能对比摘要")
    print(f"{'=' * 60}")

    for model_name, data in results_dict.items():
        if 'avg_inference_time_ms' in data:
            print(f"\n{model_name}:")
            print(f"  推理时间: {data['avg_inference_time_ms']:.2f}ms")
            print(f"  FPS: {data['fps']:.2f}")

def main():
    # 获取测试图像
    test_images = list(TEST_IMAGES_DIR.glob("*.jpg")) + list(TEST_IMAGES_DIR.glob("*.png"))
    if not test_images:
        print(f"未找到测试图像: {TEST_IMAGES_DIR}")
        return

    print(f"找到 {len(test_images)} 张测试图像")

    # 模型路径
    models_to_test = {
        "原始YOLOv8n": BASE_DIR / "models" / "yolo_unified_6class_best.pt",
        "优化YOLOv8n": BASE_DIR / "runs" / "yolo_training" / "unified_6class_optimized_n" / "weights" / "best.pt",
        "YOLOv8m": BASE_DIR / "runs" / "yolo_training" / "unified_6class_optimized_m" / "weights" / "best.pt",
        "YOLOv8n-P6": BASE_DIR / "runs" / "yolo_training" / "unified_6class_optimized_p6" / "weights" / "best.pt",
    }

    results = {}

    for model_name, model_path in models_to_test.items():
        if not model_path.exists():
            print(f"\n跳过 {model_name} - 模型文件不存在")
            continue

        model = load_model(str(model_path))
        if model is None:
            continue

        result = test_model_performance(model, test_images, model_name)
        results[model_name] = result

    # 对比混淆改善
    if "原始YOLOv8n" in results and "优化YOLOv8n" in results:
        compare_confusion_reduction(results["原始YOLOv8n"], results["优化YOLOv8n"])

    # 生成报告
    generate_comparison_report(results)

if __name__ == "__main__":
    main()
