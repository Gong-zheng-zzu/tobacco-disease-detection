"""
Data Agent - 统一YOLO数据集创建脚本
功能: 合并病害数据集(YOLO格式)和营养数据集(需生成标注),创建6类统一数据集
"""

import os
import shutil
import random
from pathlib import Path
from collections import defaultdict

# 配置路径
PROJECT_ROOT = Path(r"D:\烟草\烟草")
DISEASE_DATASET = PROJECT_ROOT / "完整-目标检测--加密--烟草叶部病害"
NUTRIENT_DATASET = PROJECT_ROOT / "模型部署数据集"
OUTPUT_DATASET = PROJECT_ROOT / "unified_tobacco_dataset"

# 类别映射 (0-3: 病害, 4-5: 营养)
CLASS_MAPPING = {
    # 病害类 (保持原有映射)
    'baixingbing': 0,
    'huayebing': 1,
    'yanqingchong': 2,
    'yehuobing': 3,
    # 营养类 (新增)
    'healthy': 4,
    'deficiency_k': 5  # 缺钾 (原"缺磷"数据集实际是缺钾)
}

def is_base_image(filename):
    """判断是否为base图像(非增强变体)"""
    augmentation_suffixes = ['_blur', '_brighter', '_darker', '_fli', '_noise', '_masked', '_r180', '_r90']
    name_without_ext = Path(filename).stem
    return not any(name_without_ext.endswith(suffix) for suffix in augmentation_suffixes)

def collect_nutrient_images():
    """收集营养数据集图像(仅base图像)"""
    nutrient_images = defaultdict(list)

    # Healthy images
    healthy_dirs = [
        NUTRIENT_DATASET / "healthy_validation_set",
        NUTRIENT_DATASET / "healthy_test_set"
    ]
    for dir_path in healthy_dirs:
        if dir_path.exists():
            for img_file in dir_path.rglob("*.jpg"):
                if is_base_image(img_file.name):
                    nutrient_images['healthy'].append(img_file)
            for img_file in dir_path.rglob("*.JPG"):
                if is_base_image(img_file.name):
                    nutrient_images['healthy'].append(img_file)

    # Deficiency_k images (原"缺磷"数据集,实际是缺钾)
    deficiency_dirs = [
        NUTRIENT_DATASET / "缺磷数据预处理_validation_set",
        NUTRIENT_DATASET / "缺磷数据预处理_test_set"
    ]
    for dir_path in deficiency_dirs:
        if dir_path.exists():
            for img_file in dir_path.rglob("*.jpg"):
                if is_base_image(img_file.name):
                    nutrient_images['deficiency_k'].append(img_file)
            for img_file in dir_path.rglob("*.JPG"):
                if is_base_image(img_file.name):
                    nutrient_images['deficiency_k'].append(img_file)

    return nutrient_images

def generate_yolo_annotation(class_id, output_file):
    """为营养图像生成YOLO标注(全图bbox)"""
    # YOLO格式: class_id center_x center_y width height (归一化坐标)
    # 全图标注: 中心点(0.5, 0.5), 宽高(1.0, 1.0)
    with open(output_file, 'w') as f:
        f.write(f"{class_id} 0.5 0.5 1.0 1.0\n")

def copy_disease_data(split_dir):
    """复制病害数据集(已有YOLO标注)"""
    disease_images = []

    # 病害数据集路径 (修正: 使用all_images和all_txt)
    image_dir = DISEASE_DATASET / "all_images"
    label_dir = DISEASE_DATASET / "all_txt"

    if not image_dir.exists() or not label_dir.exists():
        print(f"⚠️ 病害数据集路径不存在: {image_dir} 或 {label_dir}")
        return disease_images

    # 收集所有病害图像
    for img_file in image_dir.glob("*.jpg"):
        label_file = label_dir / f"{img_file.stem}.txt"
        if label_file.exists():
            disease_images.append({
                'image': img_file,
                'label': label_file,
                'class': 'disease'
            })

    # 同时检查.JPG扩展名
    for img_file in image_dir.glob("*.JPG"):
        label_file = label_dir / f"{img_file.stem}.txt"
        if label_file.exists():
            disease_images.append({
                'image': img_file,
                'label': label_file,
                'class': 'disease'
            })

    return disease_images

def split_dataset(all_data, train_ratio=0.70, val_ratio=0.15, test_ratio=0.15):
    """划分数据集: train/val/test"""
    random.shuffle(all_data)

    total = len(all_data)
    train_end = int(total * train_ratio)
    val_end = train_end + int(total * val_ratio)

    return {
        'train': all_data[:train_end],
        'val': all_data[train_end:val_end],
        'test': all_data[val_end:]
    }

def create_unified_dataset():
    """创建统一YOLO数据集"""
    print("=" * 60)
    print("Data Agent - 统一YOLO数据集创建")
    print("=" * 60)

    # 1. 收集营养数据集
    print("\n[1/6] 收集营养数据集(仅base图像)...")
    nutrient_images = collect_nutrient_images()
    print(f"  ✅ Healthy: {len(nutrient_images['healthy'])} 张")
    print(f"  ✅ Deficiency_k (缺钾): {len(nutrient_images['deficiency_k'])} 张")

    # 2. 收集病害数据集
    print("\n[2/6] 收集病害数据集...")
    disease_data = copy_disease_data("all")
    print(f"  ✅ Disease: {len(disease_data)} 张")

    # 3. 准备统一数据列表
    print("\n[3/6] 准备统一数据列表...")
    all_data = []

    # 添加病害数据
    all_data.extend(disease_data)

    # 添加营养数据
    for cls, images in nutrient_images.items():
        for img_path in images:
            all_data.append({
                'image': img_path,
                'label': None,  # 稍后生成
                'class': cls
            })

    print(f"  ✅ 总计: {len(all_data)} 张图像")

    # 4. 划分数据集
    print("\n[4/6] 划分数据集(train 70% / val 15% / test 15%)...")
    splits = split_dataset(all_data)
    print(f"  ✅ Train: {len(splits['train'])} 张")
    print(f"  ✅ Val: {len(splits['val'])} 张")
    print(f"  ✅ Test: {len(splits['test'])} 张")

    # 5. 创建目录结构
    print("\n[5/6] 创建目录结构...")
    for split in ['train', 'val', 'test']:
        (OUTPUT_DATASET / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUTPUT_DATASET / "labels" / split).mkdir(parents=True, exist_ok=True)
    print("  ✅ 目录创建完成")

    # 6. 复制文件并生成标注
    print("\n[6/6] 复制文件并生成标注...")
    stats = defaultdict(lambda: defaultdict(int))

    for split_name, data_list in splits.items():
        for idx, item in enumerate(data_list):
            # 生成唯一文件名
            if item['class'] == 'disease':
                base_name = item['image'].stem
            else:
                base_name = f"{item['class']}_{idx}"

            # 复制图像
            src_img = item['image']
            dst_img = OUTPUT_DATASET / "images" / split_name / f"{base_name}{src_img.suffix}"
            shutil.copy2(src_img, dst_img)

            # 复制或生成标注
            dst_label = OUTPUT_DATASET / "labels" / split_name / f"{base_name}.txt"
            if item['label']:  # 病害数据,已有标注
                shutil.copy2(item['label'], dst_label)
            else:  # 营养数据,生成全图标注
                class_id = CLASS_MAPPING[item['class']]
                generate_yolo_annotation(class_id, dst_label)

            # 统计
            stats[split_name][item['class']] += 1

        print(f"  ✅ {split_name}: {len(data_list)} 张完成")

    # 7. 创建data.yaml
    print("\n[7/7] 创建data.yaml...")
    yaml_content = f"""# 烟草病害&营养缺乏统一检测数据集
# 6类: 4病害 + 2营养

path: {str(OUTPUT_DATASET)}
train: images/train
val: images/val
test: images/test

names:
  0: baixingbing   # 白星病
  1: huayebing     # 黄叶病
  2: yanqingchong  # 烟青虫
  3: yehuobing     # 叶厚病
  4: healthy       # 健康
  5: deficiency_k  # 缺钾

nc: 6
"""

    yaml_path = OUTPUT_DATASET / "data.yaml"
    with open(yaml_path, 'w', encoding='utf-8') as f:
        f.write(yaml_content)
    print(f"  ✅ data.yaml 已创建: {yaml_path}")

    # 8. 生成统计报告
    print("\n" + "=" * 60)
    print("数据集创建完成 - 统计报告")
    print("=" * 60)
    print(f"\n总图像数: {len(all_data)}")
    print(f"数据集路径: {OUTPUT_DATASET}")
    print("\n各split分布:")
    for split_name in ['train', 'val', 'test']:
        print(f"  {split_name}: {len(splits[split_name])} 张")
        for cls, count in sorted(stats[split_name].items()):
            print(f"    - {cls}: {count}")

    # 生成详细报告文件
    report_path = OUTPUT_DATASET / "data_report.txt"
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Data Agent - 数据集创建报告\n")
        f.write("=" * 60 + "\n\n")
        f.write(f"总图像数: {len(all_data)}\n")
        f.write(f"数据集路径: {OUTPUT_DATASET}\n\n")
        f.write("类别定义:\n")
        for cls, idx in sorted(CLASS_MAPPING.items(), key=lambda x: x[1]):
            f.write(f"  {idx}: {cls}\n")
        f.write("\n各split分布:\n")
        for split_name in ['train', 'val', 'test']:
            f.write(f"\n{split_name}: {len(splits[split_name])} 张\n")
            for cls, count in sorted(stats[split_name].items()):
                f.write(f"  - {cls}: {count}\n")
        f.write("\n数据清理说明:\n")
        f.write("  - 移除增强变体(_blur, _brighter等),仅保留base图像\n")
        f.write("  - 修正标签错误: 原'缺磷'数据集实际为缺钾数据\n")
        f.write("  - 营养图像使用全图bbox标注(0.5 0.5 1.0 1.0)\n")

    print(f"\n详细报告已保存: {report_path}")
    print("\n✅ Data Agent 任务完成!")

if __name__ == "__main__":
    random.seed(42)  # 设置随机种子以保证可重复性
    create_unified_dataset()
