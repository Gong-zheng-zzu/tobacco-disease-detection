"""
YOLOv8-P6 小目标优化训练脚本
专门针对烟青虫小目标检测问题：
1. 使用YOLOv8n-P6（增加大分辨率检测头）
2. 输入尺寸1280x1280（提升小目标特征保留）
3. 优化数据增强策略（更激进的保护小目标）
"""
import os
from pathlib import Path
from ultralytics import YOLO

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
DATA_YAML = BASE_DIR / "unified_tobacco_dataset" / "data.yaml"
OUTPUT_DIR = BASE_DIR / "runs" / "yolo_training"

def train_yolov8_p6_for_small_objects():
    """训练YOLOv8-P6模型（专注小目标检测）"""

    print("=" * 60)
    print("开始训练 YOLOv8n-P6 小目标优化模型")
    print("=" * 60)
    print(f"数据配置: {DATA_YAML}")
    print(f"输出目录: {OUTPUT_DIR}")
    print("针对问题: 烟青虫 mAP@0.5-0.95 仅 0.594，需大幅提升")

    # 加载YOLOv8n-P6预训练模型（4个检测头，适合小目标）
    model = YOLO('yolov8n-p6.pt')

    # 训练参数（小目标优化）
    # 注意：RTX 2050显存4GB + CPU训练，大幅降低batch和分辨率
    results = model.train(
        data=str(DATA_YAML),
        epochs=100,
        imgsz=640,         # 降低分辨率640（原1280，CPU训练太慢）
        batch=2,           # CPU训练降低批量

        # 小目标保护增强策略
        mosaic=0.3,        # 大幅降低mosaic（小目标会进一步缩小）
        copy_paste=0.5,    # 大幅增加复制粘贴（放大小目标）
        scale=0.5,         # 严格限制缩放范围
        degrees=15,        # 增加旋转角度
        translate=0.2,     # 增加平移

        # 学习率策略
        lr0=0.01,
        lrf=0.001,
        warmup_epochs=5,
        cos_lr=True,

        # 损失权重（小目标优化）
        box=10.0,          # 大幅提高边界框损失权重（默认7.5）
        cls=0.5,
        dfl=2.0,           # 提高分布焦点损失（默认1.5）

        # 早停策略
        patience=30,

        # 其他参数
        device=0,          # RTX 2050 GPU可用，使用GPU训练
        workers=4,         # 降低数据加载线程（4GB显存限制）
        project=str(OUTPUT_DIR),
        name='yolov8n_p6_small_objects',
        exist_ok=True,
        pretrained=True,
        optimizer='AdamW',
        verbose=True,
        seed=42,

        # NMS参数
        conf=0.25,
        iou=0.7,
    )

    print("\n" + "=" * 60)
    print("训练完成！")
    print("=" * 60)
    print(f"最佳模型路径: {results.save_dir / 'weights' / 'best.pt'}")

    # 检查烟青虫类别性能提升
    print("\n请查看 results.csv 中 class_2 (烟青虫) 的 mAP@0.5-0.95 指标")
    print("目标: 从 0.594 提升至 0.70+")

    return results

if __name__ == "__main__":
    train_yolov8_p6_for_small_objects()
