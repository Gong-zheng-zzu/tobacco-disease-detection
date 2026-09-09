"""
烟草病害数据集分析脚本
分析 YOLO 格式标注文件，统计病害分布、检测框大小等信息
适合 Python 数据分析学习使用
"""
import os
from pathlib import Path
import pandas as pd
import matplotlib.pyplot as plt
import numpy as np
from collections import Counter

# 设置中文字体（避免图表中文显示问题）
plt.rcParams['font.sans-serif'] = ['SimHei']  # 黑体
plt.rcParams['axes.unicode_minus'] = False

# 病害类别映射
DISEASE_NAMES = {
    0: '白星病 (baixingbing)',
    1: '黄叶病 (huayebing)',
    2: '烟青虫 (yanqingchong)',
    3: '叶厚病 (yehuobing)'
}

# 数据集路径
DATASET_PATH = Path(r"烟草\完整-目标检测--加密--烟草叶部病害")
LABELS_PATH = DATASET_PATH / "all_txt"


def parse_yolo_label(label_file):
    """
    解析 YOLO 格式标注文件
    格式：class_id x_center y_center width height (归一化 0-1)
    """
    annotations = []
    if not label_file.exists():
        return annotations

    with open(label_file, 'r', encoding='utf-8') as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            if len(parts) != 5:
                continue

            class_id = int(parts[0])
            x_center = float(parts[1])
            y_center = float(parts[2])
            width = float(parts[3])
            height = float(parts[4])

            annotations.append({
                'class_id': class_id,
                'x_center': x_center,
                'y_center': y_center,
                'width': width,
                'height': height,
                'area': width * height  # 归一化面积
            })

    return annotations


def analyze_dataset():
    """分析整个数据集"""
    print("=" * 60)
    print("烟草病害数据集分析")
    print("=" * 60)

    # 检查路径
    if not LABELS_PATH.exists():
        print(f"❌ 错误：标注目录不存在 - {LABELS_PATH}")
        return

    # 获取所有标注文件
    label_files = list(LABELS_PATH.glob("*.txt"))
    total_files = len(label_files)
    print(f"\n📁 找到标注文件数量: {total_files}")

    if total_files == 0:
        print("❌ 没有找到任何标注文件")
        return

    # 存储所有标注数据
    all_annotations = []
    empty_files = 0
    objects_per_image = []

    # 遍历所有文件
    for label_file in label_files:
        annotations = parse_yolo_label(label_file)

        if len(annotations) == 0:
            empty_files += 1

        objects_per_image.append(len(annotations))
        all_annotations.extend(annotations)

    # 转换为 DataFrame
    df = pd.DataFrame(all_annotations)

    print(f"\n📊 数据集统计:")
    print(f"  总图片数: {total_files}")
    print(f"  空标注文件: {empty_files} ({empty_files/total_files*100:.1f}%)")
    print(f"  总检测目标数: {len(all_annotations)}")
    print(f"  平均每张图片目标数: {np.mean(objects_per_image):.2f}")
    print(f"  最多目标数: {max(objects_per_image)}")
    print(f"  最少目标数: {min(objects_per_image)}")

    # 病害分布统计
    print(f"\n🦠 病害类别分布:")
    class_counts = df['class_id'].value_counts().sort_index()
    for class_id, count in class_counts.items():
        disease_name = DISEASE_NAMES.get(class_id, f"未知类别 {class_id}")
        percentage = count / len(all_annotations) * 100
        print(f"  {disease_name}: {count} 个 ({percentage:.1f}%)")

    # 检测框大小统计
    print(f"\n📏 检测框尺寸统计 (归一化坐标):")
    print(f"  平均宽度: {df['width'].mean():.3f}")
    print(f"  平均高度: {df['height'].mean():.3f}")
    print(f"  平均面积: {df['area'].mean():.3f}")
    print(f"  最小面积: {df['area'].min():.3f}")
    print(f"  最大面积: {df['area'].max():.3f}")

    # 各病害的平均尺寸
    print(f"\n📐 各病害平均检测框面积:")
    for class_id in sorted(df['class_id'].unique()):
        disease_name = DISEASE_NAMES.get(class_id, f"未知 {class_id}")
        avg_area = df[df['class_id'] == class_id]['area'].mean()
        print(f"  {disease_name}: {avg_area:.3f}")

    # 可视化
    visualize_results(df, class_counts, objects_per_image)

    return df


def visualize_results(df, class_counts, objects_per_image):
    """数据可视化"""
    fig, axes = plt.subplots(2, 2, figsize=(14, 10))
    fig.suptitle('烟草病害数据集分析结果', fontsize=16, fontweight='bold')

    # 1. 病害分布饼图
    ax1 = axes[0, 0]
    labels = [DISEASE_NAMES.get(i, f'类别{i}') for i in class_counts.index]
    colors = ['#ff9999', '#66b3ff', '#99ff99', '#ffcc99']
    ax1.pie(class_counts.values, labels=labels, autopct='%1.1f%%',
            colors=colors, startangle=90)
    ax1.set_title('病害类别分布')

    # 2. 病害数量柱状图
    ax2 = axes[0, 1]
    labels_short = [DISEASE_NAMES[i].split()[0] for i in class_counts.index]
    bars = ax2.bar(labels_short, class_counts.values, color=colors)
    ax2.set_title('各类病害检测目标数量')
    ax2.set_xlabel('病害类型')
    ax2.set_ylabel('数量')
    ax2.grid(axis='y', alpha=0.3)

    # 在柱子上标注数值
    for bar in bars:
        height = bar.get_height()
        ax2.text(bar.get_x() + bar.get_width()/2., height,
                f'{int(height)}',
                ha='center', va='bottom')

    # 3. 每张图片目标数分布
    ax3 = axes[1, 0]
    ax3.hist(objects_per_image, bins=range(0, max(objects_per_image)+2),
             color='skyblue', edgecolor='black', alpha=0.7)
    ax3.set_title('每张图片检测目标数分布')
    ax3.set_xlabel('目标数量')
    ax3.set_ylabel('图片数量')
    ax3.grid(axis='y', alpha=0.3)

    # 4. 检测框面积分布（各病害）
    ax4 = axes[1, 1]
    for class_id in sorted(df['class_id'].unique()):
        disease_name = DISEASE_NAMES.get(class_id, f'类别{class_id}').split()[0]
        areas = df[df['class_id'] == class_id]['area']
        ax4.hist(areas, bins=30, alpha=0.5, label=disease_name)

    ax4.set_title('检测框面积分布（各病害）')
    ax4.set_xlabel('归一化面积')
    ax4.set_ylabel('数量')
    ax4.legend()
    ax4.grid(axis='y', alpha=0.3)

    plt.tight_layout()

    # 保存图表
    output_path = Path("烟草_数据集分析结果.png")
    plt.savefig(output_path, dpi=300, bbox_inches='tight')
    print(f"\n💾 分析图表已保存: {output_path.absolute()}")

    plt.show()


def export_statistics(df):
    """导出统计数据到 CSV"""
    if df is None or len(df) == 0:
        return

    # 按病害类别统计
    summary = df.groupby('class_id').agg({
        'width': ['mean', 'std', 'min', 'max'],
        'height': ['mean', 'std', 'min', 'max'],
        'area': ['mean', 'std', 'min', 'max'],
        'class_id': 'count'
    }).round(4)

    summary.columns = ['_'.join(col).strip() for col in summary.columns.values]
    summary = summary.rename(columns={'class_id_count': 'total_count'})
    summary['disease_name'] = [DISEASE_NAMES.get(i, f'未知{i}') for i in summary.index]

    output_csv = Path("烟草_病害统计.csv")
    summary.to_csv(output_csv, encoding='utf-8-sig')
    print(f"📄 统计数据已导出: {output_csv.absolute()}")


if __name__ == "__main__":
    df = analyze_dataset()

    if df is not None and len(df) > 0:
        export_statistics(df)
        print("\n✅ 分析完成！")
    else:
        print("\n❌ 分析失败，请检查数据集路径")
