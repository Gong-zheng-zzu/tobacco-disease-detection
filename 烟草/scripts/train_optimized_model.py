"""
优化模型训练脚本 - Phase 6 Algorithm Optimization
基于实验报告分析，针对性优化：
1. 烟青虫小目标检测（mosaic降低、copy_paste启用）
2. 白星病-花叶病混淆（色调/饱和度增强）
3. 数据不平衡（mixup混合）
"""
import os
from ultralytics import YOLO

# 路径配置
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_YAML = os.path.join(BASE_DIR, "unified_tobacco_dataset", "data.yaml")
OUTPUT_DIR = os.path.join(BASE_DIR, "runs", "yolo_training")

def train_optimized_yolov8n():
    """训练优化版YOLOv8n（数据增强调整）"""
    print("=" * 60)
    print("训练优化版YOLOv8n - 针对小目标和类别混淆")
    print("=" * 60)

    model = YOLO('yolov8n.pt')

    results = model.train(
        data=DATA_YAML,
        epochs=100,
        imgsz=640,
        batch=16,
        # 优化的数据增强参数
        mosaic=0.5,        # 降低mosaic（从1.0→0.5），保护小目标
        copy_paste=0.3,    # 启用copy_paste，增强小目标
        scale=0.7,         # 减少缩放范围（从0.5→0.7），保护小目标尺寸
        mixup=0.15,        # 启用mixup，缓解数据不平衡
        hsv_h=0.015,       # 增加色调抖动，区分白星病/花叶病
        hsv_s=0.7,         # 增加饱和度抖动
        hsv_v=0.4,         # 亮度抖动
        # 标准参数
        device=0,
        workers=4,
        patience=50,
        save=True,
        project=OUTPUT_DIR,
        name='unified_6class_optimized_n',
        exist_ok=True,
    )

    print("\n训练完成！")
    print(f"最佳权重: {results.save_dir}/weights/best.pt")
    return results

def train_yolov8m():
    """训练YOLOv8m（更大模型，更高精度）"""
    print("=" * 60)
    print("训练YOLOv8m - 25.9M参数，高精度模型")
    print("=" * 60)

    model = YOLO('yolov8m.pt')

    results = model.train(
        data=DATA_YAML,
        epochs=80,  # 更大模型，减少轮数避免过拟合
        imgsz=640,
        batch=8,    # 更大模型，减少batch size
        # 使用优化的数据增强
        mosaic=0.5,
        copy_paste=0.3,
        scale=0.7,
        mixup=0.15,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        # 标准参数
        device=0,
        workers=4,
        patience=30,  # 更早停止
        save=True,
        project=OUTPUT_DIR,
        name='unified_6class_optimized_m',
        exist_ok=True,
    )

    print("\n训练完成！")
    print(f"最佳权重: {results.save_dir}/weights/best.pt")
    return results

def train_yolov8_p6():
    """训练YOLOv8-P6（高分辨率，专攻小目标）"""
    print("=" * 60)
    print("训练YOLOv8n-P6 - 1280分辨率，4个检测头")
    print("=" * 60)

    model = YOLO('yolov8n-p6.pt')

    results = model.train(
        data=DATA_YAML,
        epochs=100,
        imgsz=1280,  # 高分辨率
        batch=4,     # 高分辨率需要更小batch
        # 优化的数据增强
        mosaic=0.5,
        copy_paste=0.3,
        scale=0.7,
        mixup=0.15,
        hsv_h=0.015,
        hsv_s=0.7,
        hsv_v=0.4,
        # 标准参数
        device=0,
        workers=4,
        patience=50,
        save=True,
        project=OUTPUT_DIR,
        name='unified_6class_optimized_p6',
        exist_ok=True,
    )

    print("\n训练完成！")
    print(f"最佳权重: {results.save_dir}/weights/best.pt")
    return results

if __name__ == "__main__":
    import argparse
    parser = argparse.ArgumentParser(description="训练优化模型")
    parser.add_argument(
        '--model',
        type=str,
        choices=['n', 'm', 'p6', 'all'],
        default='n',
        help='选择训练模型: n=YOLOv8n优化版, m=YOLOv8m, p6=YOLOv8n-P6, all=全部训练'
    )
    args = parser.parse_args()

    if args.model == 'n':
        train_optimized_yolov8n()
    elif args.model == 'm':
        train_yolov8m()
    elif args.model == 'p6':
        train_yolov8_p6()
    elif args.model == 'all':
        print("依次训练所有优化模型...\n")
        train_optimized_yolov8n()
        print("\n" + "=" * 60 + "\n")
        train_yolov8m()
        print("\n" + "=" * 60 + "\n")
        train_yolov8_p6()
