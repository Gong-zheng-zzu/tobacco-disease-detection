"""
烟草叶部病害目标检测 - YOLOv8 训练脚本
数据集: 完整-目标检测--加密--烟草叶部病害
"""
import os
import shutil
from pathlib import Path

try:
    from ultralytics import YOLO
except ImportError:
    print("请先安装 ultralytics: pip install ultralytics")
    exit(1)

# 工作目录
SCRIPT_DIR = Path(__file__).resolve().parent
PROJECT_DIR = SCRIPT_DIR
DATA_YAML = SCRIPT_DIR / "data.yaml"

# 训练参数
EPOCHS = 30
BATCH = 16
IMG_SIZE = 640
MODEL_NAME = "yolov8n.pt"  # n/s/m/l/x 可选，n 最快、x 精度最高


def main():
    if not DATA_YAML.exists():
        print(f"未找到 data.yaml: {DATA_YAML}")
        print("请确认 data.yaml 存在且 path 指向正确的数据集路径")
        return

    model = YOLO(MODEL_NAME)
    results = model.train(
        data=str(DATA_YAML),
        epochs=EPOCHS,
        batch=BATCH,
        imgsz=IMG_SIZE,
        project=str(PROJECT_DIR),
        name="runs/train",
        exist_ok=True,
        pretrained=True,
        patience=20,
        verbose=True,
    )

    # 训练完成后，最佳权重在 runs/train/weights/best.pt
    best_pt = PROJECT_DIR / "runs" / "train" / "weights" / "best.pt"
    last_pt = PROJECT_DIR / "runs" / "train" / "weights" / "last.pt"
    print("\n训练完成!")
    if best_pt.exists():
        print(f"最佳模型: {best_pt}")
        # 同步到 Django 后端推理目录，供 drf_test002 加载
        deploy_pt = PROJECT_DIR.parent / "前后端" / "drf_test002" / "model_weights" / "yolov8n_best.pt"
        try:
            deploy_pt.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(best_pt, deploy_pt)
            print(f"已复制到后端: {deploy_pt}")
        except OSError as e:
            print(f"复制到后端失败（可手动复制 best.pt 为 yolov8n_best.pt）: {e}")
    if last_pt.exists():
        print(f"最新模型: {last_pt}")


if __name__ == "__main__":
    main()
