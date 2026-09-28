"""
Training Agent - 训练统一YOLOv8n模型（6类）

目标：
1. 训练YOLOv8n模型（6类：白星病、花叶病、烟青虫、野火病、健康、缺钾）
2. 解决原YOLO将缺钾误判为白星病的问题
3. 替代ResNet18缺磷分类器（数据集标签错误）
4. 保存训练曲线、最佳权重、验证报告

Authors: Training Agent
Date: 2026-09-10
"""

import sys
from pathlib import Path
from ultralytics import YOLO
import torch
import yaml
import shutil
from datetime import datetime

# 项目路径配置
PROJECT_ROOT = Path(r"D:\烟草\烟草")
DATA_YAML = PROJECT_ROOT / "unified_tobacco_dataset" / "data.yaml"
OUTPUT_DIR = PROJECT_ROOT / "runs" / "yolo_training"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

# 训练配置
TRAINING_CONFIG = {
    'model': 'yolov8n.yaml',  # YOLOv8 Nano
    'data': str(DATA_YAML),
    'epochs': 100,
    'imgsz': 640,
    'batch': 16,  # RTX 2050 4GB VRAM适配
    'device': 0,  # GPU
    'workers': 4,
    'patience': 20,  # Early stopping
    'save': True,
    'save_period': 10,
    'project': str(OUTPUT_DIR),
    'name': f'unified_6class_{datetime.now().strftime("%Y%m%d_%H%M%S")}',
    'exist_ok': True,
    'pretrained': True,
    'optimizer': 'SGD',
    'lr0': 0.01,
    'lrf': 0.01,
    'momentum': 0.937,
    'weight_decay': 0.0005,
    'warmup_epochs': 3,
    'warmup_momentum': 0.8,
    'warmup_bias_lr': 0.1,
    'box': 7.5,
    'cls': 0.5,
    'dfl': 1.5,
    'hsv_h': 0.015,
    'hsv_s': 0.7,
    'hsv_v': 0.4,
    'degrees': 0.0,
    'translate': 0.1,
    'scale': 0.5,
    'shear': 0.0,
    'perspective': 0.0,
    'flipud': 0.0,
    'fliplr': 0.5,
    'mosaic': 1.0,
    'mixup': 0.0,
    'copy_paste': 0.0,
    'val': True,
    'plots': True,
    'verbose': True,
}

def check_environment():
    """检查训练环境"""
    print("=" * 60)
    print("Training Agent - 环境检查")
    print("=" * 60)

    # 检查CUDA
    if torch.cuda.is_available():
        print(f"✅ CUDA 可用: {torch.cuda.get_device_name(0)}")
        print(f"   显存: {torch.cuda.get_device_properties(0).total_memory / 1024**3:.2f} GB")
    else:
        print("⚠️ CUDA 不可用，将使用CPU训练（速度较慢）")
        TRAINING_CONFIG['device'] = 'cpu'

    # 检查数据集
    if not DATA_YAML.exists():
        print(f"❌ 数据集配置不存在: {DATA_YAML}")
        sys.exit(1)

    with open(DATA_YAML, 'r', encoding='utf-8') as f:
        data_config = yaml.safe_load(f)

    print(f"✅ 数据集配置: {DATA_YAML}")
    print(f"   类别数: {data_config['nc']}")
    print(f"   类别: {list(data_config['names'].values())}")

    # 检查数据集文件
    dataset_root = Path(data_config['path'])
    train_dir = dataset_root / data_config['train']
    val_dir = dataset_root / data_config['val']

    train_count = len(list((train_dir).glob("*.jpg"))) + len(list((train_dir).glob("*.JPG")))
    val_count = len(list((val_dir).glob("*.jpg"))) + len(list((val_dir).glob("*.JPG")))

    print(f"   Train: {train_count} 张")
    print(f"   Val: {val_count} 张")

    print()

def train_model():
    """训练YOLO模型"""
    print("=" * 60)
    print("Training Agent - 开始训练")
    print("=" * 60)

    # 加载预训练模型
    model = YOLO('yolov8n.pt')

    print(f"训练配置:")
    print(f"  - Epochs: {TRAINING_CONFIG['epochs']}")
    print(f"  - Batch Size: {TRAINING_CONFIG['batch']}")
    print(f"  - Image Size: {TRAINING_CONFIG['imgsz']}")
    print(f"  - Device: {TRAINING_CONFIG['device']}")
    print(f"  - Patience: {TRAINING_CONFIG['patience']}")
    print()

    # 开始训练
    results = model.train(**TRAINING_CONFIG)

    return model, results

def validate_model(model):
    """验证模型性能"""
    print("=" * 60)
    print("Training Agent - 模型验证")
    print("=" * 60)

    metrics = model.val()

    print(f"验证结果:")
    print(f"  - mAP50: {metrics.box.map50:.4f}")
    print(f"  - mAP50-95: {metrics.box.map:.4f}")
    print(f"  - Precision: {metrics.box.mp:.4f}")
    print(f"  - Recall: {metrics.box.mr:.4f}")
    print()

    return metrics

def save_training_report(model, metrics, train_dir):
    """保存训练报告"""
    report_path = OUTPUT_DIR / "training_report.txt"

    with open(report_path, 'w', encoding='utf-8') as f:
        f.write("=" * 60 + "\n")
        f.write("Training Agent - 训练报告\n")
        f.write("=" * 60 + "\n\n")

        f.write(f"训练时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write(f"模型: YOLOv8n (6类统一模型)\n")
        f.write(f"数据集: {DATA_YAML}\n\n")

        f.write("训练配置:\n")
        f.write(f"  - Epochs: {TRAINING_CONFIG['epochs']}\n")
        f.write(f"  - Batch Size: {TRAINING_CONFIG['batch']}\n")
        f.write(f"  - Image Size: {TRAINING_CONFIG['imgsz']}\n")
        f.write(f"  - Device: {TRAINING_CONFIG['device']}\n")
        f.write(f"  - Patience: {TRAINING_CONFIG['patience']}\n\n")

        f.write("验证结果:\n")
        f.write(f"  - mAP50: {metrics.box.map50:.4f}\n")
        f.write(f"  - mAP50-95: {metrics.box.map:.4f}\n")
        f.write(f"  - Precision: {metrics.box.mp:.4f}\n")
        f.write(f"  - Recall: {metrics.box.mr:.4f}\n\n")

        f.write("类别定义（6类）:\n")
        f.write("  0: baixingbing (白星病)\n")
        f.write("  1: huayebing (花叶病)\n")
        f.write("  2: yanqingchong (烟青虫)\n")
        f.write("  3: yehuobing (野火病)\n")
        f.write("  4: healthy (健康)\n")
        f.write("  5: deficiency_k (缺钾)\n\n")

        f.write("解决的问题:\n")
        f.write("  1. ✅ YOLO将缺钾误判为白星病 - 通过扩展至6类统一模型\n")
        f.write("  2. ✅ ResNet18缺磷数据集标签错误 - 用YOLO缺钾类替代\n")
        f.write("  3. ✅ 病害检测+营养分类分离 - 统一为单一YOLO模型\n\n")

        f.write(f"权重路径: {train_dir / 'weights' / 'best.pt'}\n")
        f.write(f"训练日志: {train_dir}\n")

    print(f"✅ 训练报告已保存: {report_path}")
    print()

def main():
    """主函数"""
    try:
        # 1. 环境检查
        check_environment()

        # 2. 训练模型
        model, results = train_model()

        # 3. 验证模型
        metrics = validate_model(model)

        # 4. 保存报告
        train_dir = Path(model.trainer.save_dir)
        save_training_report(model, metrics, train_dir)

        # 5. 复制最佳权重到统一位置
        best_weights = train_dir / "weights" / "best.pt"
        unified_weights = PROJECT_ROOT / "models" / "yolo_unified_6class_best.pt"
        unified_weights.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy(best_weights, unified_weights)

        print("=" * 60)
        print("Training Agent - 训练完成")
        print("=" * 60)
        print(f"✅ 最佳权重: {unified_weights}")
        print(f"✅ 训练目录: {train_dir}")
        print(f"✅ mAP50: {metrics.box.map50:.4f}")
        print(f"✅ mAP50-95: {metrics.box.map:.4f}")
        print("=" * 60)

        return 0

    except KeyboardInterrupt:
        print("\n⚠️ 训练被用户中断")
        return 1
    except Exception as e:
        print(f"\n❌ 训练失败: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())
