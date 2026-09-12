"""
YOLOv8m 优化训练脚本
针对算法瓶颈进行优化：
1. 升级到YOLOv8m（更大模型，更强检测能力）
2. 优化数据增强策略（降低mosaic，保护小目标）
3. 调整损失权重（增强小目标检测）
4. 使用余弦退火学习率
"""
import os
from pathlib import Path
from ultralytics import YOLO

# 项目根目录
BASE_DIR = Path(__file__).parent.parent
DATA_YAML = BASE_DIR / "unified_tobacco_dataset" / "unified_tobacco.yaml"
OUTPUT_DIR = BASE_DIR / "runs" / "yolo_training"

def train_yolov8m_optimized():
    """训练优化后的YOLOv8m模型"""

    print("=" * 60)
    print("开始训练 YOLOv8m 优化模型")
    print("=" * 60)
    print(f"数据配置: {DATA_YAML}")
    print(f"输出目录: {OUTPUT_DIR}")

    # 加载YOLOv8m预训练模型
    model = YOLO('yolov8m.pt')

    # 训练参数（针对算法瓶颈优化）
    # 注意：RTX 2050显存4GB，需要降低batch size
    results = model.train(
        data=str(DATA_YAML),
        epochs=100,
        imgsz=640,
        batch=4,  # RTX 2050显存限制，降低批量（原16→4）

        # 优化后的数据增强策略
        mosaic=0.5,        # 降低mosaic概率（默认1.0），保护小目标
        copy_paste=0.3,    # 启用复制粘贴增强，放大小目标
        scale=0.7,         # 减少缩放范围，避免小目标过度缩小
        mixup=0.1,         # 添加mixup增强

        # 学习率策略优化
        lr0=0.01,          # 初始学习率
        lrf=0.001,         # 最终学习率因子（比默认0.01更低，让后期探索更充分）
        warmup_epochs=5,   # 预热轮数（增加到5）
        cos_lr=True,       # 使用余弦退火学习率

        # 损失权重调整（增强边界框和小目标检测）
        box=7.5,           # 边界框损失权重
        cls=0.5,           # 分类损失权重
        dfl=1.5,           # 分布焦点损失

        # 早停策略
        patience=30,       # 30轮无提升则停止

        # 其他参数
        device='cpu',      # RTX 2050 CUDA不可用，使用CPU训练
        workers=8,
        project=str(OUTPUT_DIR),
        name='yolov8m_optimized',
        exist_ok=True,
        pretrained=True,
        optimizer='AdamW',
        verbose=True,
        seed=42,

        # NMS参数（推理时）
        conf=0.25,
        iou=0.7,
    )

    print("\n" + "=" * 60)
    print("训练完成！")
    print("=" * 60)
    print(f"最佳模型路径: {results.save_dir / 'weights' / 'best.pt'}")
    print(f"mAP@0.5: {results.results_dict.get('metrics/mAP50(B)', 'N/A')}")
    print(f"mAP@0.5-0.95: {results.results_dict.get('metrics/mAP50-95(B)', 'N/A')}")

    return results

if __name__ == "__main__":
    train_yolov8m_optimized()
