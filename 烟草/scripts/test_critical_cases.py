#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
关键案例测试：验证缺钾样本不被误判为白星病
"""
import os
import sys
from pathlib import Path
from ultralytics import YOLO
import random

# 类别映射
CLASS_NAMES = {
    0: 'baixingbing',    # 白星病
    1: 'huayebing',      # 花叶病
    2: 'yanqingchong',   # 烟青虫
    3: 'yehuobing',      # 野火病
    4: 'healthy',        # 健康
    5: 'deficiency_k'    # 缺钾
}

CLASS_CN = {
    'baixingbing': '白星病',
    'huayebing': '花叶病',
    'yanqingchong': '烟青虫',
    'yehuobing': '野火病',
    'healthy': '健康',
    'deficiency_k': '缺钾'
}

def test_critical_cases():
    """测试关键案例：缺钾样本识别准确性"""

    # 加载模型
    model_path = r'D:\烟草\烟草\models\yolo_unified_6class_best.pt'
    model = YOLO(model_path)

    # 缺钾测试集路径
    test_images_dir = Path(r'D:\烟草\烟草\unified_tobacco_dataset\images\test')

    # 从测试集标签文件中找到所有缺钾样本
    test_labels_dir = Path(r'D:\烟草\烟草\unified_tobacco_dataset\labels\test')

    deficiency_k_images = []
    baixingbing_images = []

    for label_file in test_labels_dir.glob('*.txt'):
        with open(label_file, 'r') as f:
            lines = f.readlines()
            if lines:
                first_class = int(lines[0].split()[0])
                image_name = label_file.stem + '.jpg'
                image_path = test_images_dir / image_name

                if image_path.exists():
                    if first_class == 5:  # 缺钾
                        deficiency_k_images.append(image_path)
                    elif first_class == 0:  # 白星病
                        baixingbing_images.append(image_path)

    print(f"\n{'='*60}")
    print(f"找到缺钾测试样本: {len(deficiency_k_images)} 张")
    print(f"找到白星病测试样本: {len(baixingbing_images)} 张")
    print(f"{'='*60}\n")

    # 测试1: 所有缺钾样本
    print(f"\n{'='*60}")
    print("测试1: 缺钾样本识别准确性（最关键！）")
    print(f"{'='*60}")

    correct_k = 0
    wrong_as_baixing = 0
    wrong_as_other = 0

    for img_path in deficiency_k_images:
        results = model.predict(img_path, conf=0.25, verbose=False)

        if len(results[0].boxes) > 0:
            pred_class = int(results[0].boxes.cls[0])
            pred_conf = float(results[0].boxes.conf[0])
            pred_name = CLASS_NAMES[pred_class]

            if pred_class == 5:  # 正确识别为缺钾
                correct_k += 1
            elif pred_class == 0:  # 误判为白星病
                wrong_as_baixing += 1
                print(f"❌ 误判为白星病: {img_path.name} (置信度: {pred_conf:.3f})")
            else:
                wrong_as_other += 1
                print(f"⚠️  误判为{CLASS_CN[pred_name]}: {img_path.name} (置信度: {pred_conf:.3f})")
        else:
            print(f"⚠️  未检测到目标: {img_path.name}")

    k_accuracy = correct_k / len(deficiency_k_images) * 100
    baixing_error_rate = wrong_as_baixing / len(deficiency_k_images) * 100

    print(f"\n缺钾识别结果:")
    print(f"  ✅ 正确识别: {correct_k}/{len(deficiency_k_images)} ({k_accuracy:.2f}%)")
    print(f"  ❌ 误判为白星病: {wrong_as_baixing}/{len(deficiency_k_images)} ({baixing_error_rate:.2f}%)")
    print(f"  ⚠️  误判为其他: {wrong_as_other}/{len(deficiency_k_images)}")

    # 测试2: 随机抽样白星病样本（确保白星病识别不受影响）
    print(f"\n{'='*60}")
    print("测试2: 白星病样本识别准确性（对照组）")
    print(f"{'='*60}")

    sample_baixing = random.sample(baixingbing_images, min(20, len(baixingbing_images)))
    correct_baixing = 0
    wrong_baixing = 0

    for img_path in sample_baixing:
        results = model.predict(img_path, conf=0.25, verbose=False)

        if len(results[0].boxes) > 0:
            pred_class = int(results[0].boxes.cls[0])
            pred_conf = float(results[0].boxes.conf[0])
            pred_name = CLASS_NAMES[pred_class]

            if pred_class == 0:
                correct_baixing += 1
            else:
                wrong_baixing += 1
                print(f"❌ 白星病误判为{CLASS_CN[pred_name]}: {img_path.name} (置信度: {pred_conf:.3f})")

    baixing_accuracy = correct_baixing / len(sample_baixing) * 100
    print(f"\n白星病识别结果 (样本{len(sample_baixing)}张):")
    print(f"  ✅ 正确识别: {correct_baixing}/{len(sample_baixing)} ({baixing_accuracy:.2f}%)")
    print(f"  ❌ 误判: {wrong_baixing}/{len(sample_baixing)}")

    # 最终总结
    print(f"\n{'='*60}")
    print("✅ 实验验证总结")
    print(f"{'='*60}")
    print(f"1. 缺钾识别准确率: {k_accuracy:.2f}% (目标: >95%)")
    print(f"2. 缺钾→白星病误判率: {baixing_error_rate:.2f}% (目标: <5%)")
    print(f"3. 白星病识别准确率: {baixing_accuracy:.2f}%")

    if k_accuracy >= 95 and baixing_error_rate <= 5:
        print(f"\n🎉 测试通过！模型成功解决了缺钾误判为白星病的问题！")
        return True
    else:
        print(f"\n⚠️  测试未达标，需要进一步优化")
        return False

if __name__ == '__main__':
    success = test_critical_cases()
    sys.exit(0 if success else 1)
