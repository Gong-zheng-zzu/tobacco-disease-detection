"""
分析白星病-花叶病混淆情况
找出同时检测到两类的样本数量
"""
from pathlib import Path
from ultralytics import YOLO

BASE_DIR = Path(__file__).resolve().parent.parent
MODEL_PATH = BASE_DIR / "前后端" / "drf_test002" / "model_weights" / "yolo_unified_6class_best.pt"
DATASET_DIR = BASE_DIR / "unified_tobacco_dataset"

CLASS_NAMES = {
    0: 'baixingbing',
    1: 'huayebing',
    2: 'yanqingchong',
    3: 'yehuobing',
    4: 'healthy',
    5: 'deficiency_k'
}

print("加载模型...")
model = YOLO(str(MODEL_PATH))

images_dir = DATASET_DIR / 'images' / 'test'
labels_dir = DATASET_DIR / 'labels' / 'test'

image_files = list(images_dir.glob('*.jpg')) + list(images_dir.glob('*.png'))

confusion_cases = []
baixingbing_only = 0
huayebing_only = 0
both_detected = 0

print(f"分析 {len(image_files)} 个测试样本...\n")

for img_path in image_files:
    # 读取真实标签
    label_path = labels_dir / f"{img_path.stem}.txt"
    if not label_path.exists():
        continue

    ground_truth = set()
    with open(label_path, 'r') as f:
        for line in f:
            parts = line.strip().split()
            if parts:
                cls_id = int(parts[0])
                if cls_id in CLASS_NAMES:
                    ground_truth.add(CLASS_NAMES[cls_id])

    # 模型推理
    results = model.predict(
        source=str(img_path),
        conf=0.35,
        iou=0.4,
        agnostic_nms=True,
        verbose=False
    )

    detected = set()
    confidences = {}

    for r in results:
        if r.boxes is not None and len(r.boxes) > 0:
            for box_idx in range(len(r.boxes)):
                cls_id = int(r.boxes.cls[box_idx])
                conf = float(r.boxes.conf[box_idx])

                if cls_id in CLASS_NAMES:
                    class_name = CLASS_NAMES[cls_id]
                    detected.add(class_name)
                    if class_name not in confidences or conf > confidences[class_name]:
                        confidences[class_name] = conf

    # 统计混淆情况
    has_baixing = 'baixingbing' in detected
    has_huaye = 'huayebing' in detected

    if has_baixing and has_huaye:
        both_detected += 1
        conf_diff = abs(confidences['baixingbing'] - confidences['huayebing'])
        confusion_cases.append({
            'image': img_path.name,
            'ground_truth': ground_truth,
            'baixing_conf': confidences['baixingbing'],
            'huaye_conf': confidences['huayebing'],
            'conf_diff': conf_diff
        })
    elif has_baixing:
        baixingbing_only += 1
    elif has_huaye:
        huayebing_only += 1

print("="*70)
print("白星病-花叶病混淆分析")
print("="*70)
print(f"仅检测到白星病: {baixingbing_only} 样本")
print(f"仅检测到花叶病: {huayebing_only} 样本")
print(f"同时检测到两类: {both_detected} 样本")
print(f"\n混淆率: {both_detected / (baixingbing_only + huayebing_only + both_detected) * 100:.2f}%")

if confusion_cases:
    print(f"\n前10个混淆案例:")
    print("-"*70)
    for i, case in enumerate(confusion_cases[:10], 1):
        print(f"{i}. {case['image']}")
        print(f"   真实标签: {case['ground_truth']}")
        print(f"   白星病置信度: {case['baixing_conf']:.3f}")
        print(f"   花叶病置信度: {case['huaye_conf']:.3f}")
        print(f"   置信度差: {case['conf_diff']:.3f}")
        print()
