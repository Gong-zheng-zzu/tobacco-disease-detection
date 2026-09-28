#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试单张图像的检测结果
"""
from ultralytics import YOLO
from pathlib import Path

# 类别映射
CLASS_NAMES = {
    0: 'baixingbing',
    1: 'huayebing',
    2: 'yanqingchong',
    3: 'yehuobing',
    4: 'healthy',
    5: 'deficiency_k'
}

CLASS_CN = {
    'baixingbing': '白星病',
    'huayebing': '花叶病',
    'yanqingchong': '烟青虫',
    'yehuobing': '野火病',
    'healthy': '健康',
    'deficiency_k': '缺钾'
}

# 加载模型
model_path = r'D:\烟草\烟草\models\yolo_unified_6class_best.pt'
print(f"加载模型: {model_path}")
model = YOLO(model_path)

# 测试图像
test_images = [
    r'D:\烟草\烟草\unified_tobacco_dataset\images\test\deficiency_k_1.jpg',
    r'D:\烟草\烟草\unified_tobacco_dataset\images\test\healthy_0.jpg',
    r'D:\烟草\烟草\unified_tobacco_dataset\images\test\Tobacco_Disease_100001.jpg',
]

for img_path in test_images:
    img_file = Path(img_path)
    if not img_file.exists():
        print(f"\n❌ 图像不存在: {img_path}")
        continue

    print(f"\n{'='*60}")
    print(f"测试: {img_file.name}")
    print(f"{'='*60}")

    results = model.predict(img_path, conf=0.25, verbose=False)

    if len(results[0].boxes) == 0:
        print("⚠️  未检测到任何目标")
    else:
        print(f"检测到 {len(results[0].boxes)} 个目标:")
        for i, box in enumerate(results[0].boxes):
            cls_id = int(box.cls[0])
            conf = float(box.conf[0])
            class_name = CLASS_NAMES.get(cls_id, 'unknown')
            class_cn = CLASS_CN.get(class_name, 'unknown')
            print(f"  [{i+1}] {class_cn} (ID={cls_id}, 置信度={conf:.3f})")
