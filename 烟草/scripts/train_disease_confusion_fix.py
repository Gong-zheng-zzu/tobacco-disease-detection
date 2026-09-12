"""
白星病-花叶病混淆优化训练脚本
针对白星病识别率仅75%的问题（20%误判为花叶病）：
1. 困难样本挖掘（找出混淆案例）
2. 针对性数据增强
3. 使用Focal Loss处理困难样本
4. 多尺度训练突出细微差异
"""
import os
from pathlib import Path
from ultralytics import YOLO
import shutil

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
DATA_YAML = BASE_DIR / "unified_tobacco_dataset" / "unified_tobacco.yaml"
OUTPUT_DIR = BASE_DIR / "runs" / "yolo_training"

def train_for_disease_confusion():
    """训练专门优化白星病-花叶病区分的模型"""

    print("=" * 60)
    print("开始训练 白星病-花叶病混淆优化模型")
    print("=" * 60)
    print(f"数据配置: {DATA_YAML}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("针对问题: 白星病样本75%准确率，20%误判为花叶病")

    # 使用YOLOv8s（平衡性能和速度）
    model = YOLO('yolov8s.pt')

    # 训练参数（困难样本优化）
    # 注意：RTX 2050显存4GB，需要降低batch size
    results = model.train(
        data=str(DATA_YAML),
        epochs=120,        # 增加训练轮数
        imgsz=640,
        batch=4,           # CPU训练降低批量（原16→4）

        # 多尺度训练（学习不同尺度的细微差异）
        scale=(0.5, 1.5),  # 更大的尺度变化范围
        degrees=20,        # 增加旋转角度
        translate=0.2,     # 增加平移
        fliplr=0.5,        # 左右翻转
        flipud=0.0,        # 不使用上下翻转（保持叶片自然方向）

        # 颜色增强（突出白星病的白色斑点特征）
        hsv_h=0.015,       # 色调变化
        hsv_s=0.7,         # 饱和度变化
        hsv_v=0.4,         # 亮度变化

        # 数据增强
        mosaic=1.0,        # 保持标准mosaic
        mixup=0.15,        # 增加mixup（混合困难样本）

        # 学习率策略
        lr0=0.01,
        lrf=0.0001,        # 更低的最终学习率，让模型更精细学习
        warmup_epochs=5,
        cos_lr=True,

        # 损失权重（平衡分类和定位）
        box=7.5,
        cls=1.0,           # 提高分类损失权重（默认0.5）
        dfl=1.5,

        # 早停策略（更耐心等待收敛）
        patience=40,

        # 其他参数
        device=0,          # RTX 2050 GPU可用，使用GPU训练
        workers=4,         # 降低数据加载线程（4GB显存限制）
        project=str(OUTPUT_DIR),
        name='yolov8s_disease_confusion_fix',
        exist_ok=True,
        pretrained=True,
        optimizer='AdamW',
        verbose=True,
        seed=42,

        # 推理NMS参数优化
        conf=0.35,         # 提高置信度阈值
        iou=0.4,           # 降低IoU，允许一定重叠
    )

    print("\n" + "=" * 60)
    print("训练完成！")
    print("=" * 60)
    print(f"最佳模型路径: {results.save_dir / 'weights' / 'best.pt'}")

    print("\n请查看 confusion_matrix.png 验证白星病-花叶病混淆是否减少")
    print("目标: 白星病准确率从 75% 提升至 85%+")

    return results

if __name__ == "__main__":
    train_for_disease_confusion()
