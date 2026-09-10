# 烟草叶部病害目标检测 - YOLO

基于 YOLOv8 的烟草叶部病害目标检测，数据集为「完整-目标检测--加密--烟草叶部病害」。

## 目录结构

```
E:\烟草\disease\
├── data.yaml          # 数据集配置
├── train_yolo.py      # 训练脚本
├── predict_yolo.py    # 推理脚本
├── split_dataset.py   # 数据集划分工具（若未划分）
├── requirements.txt   # 依赖
└── runs/              # 训练输出、检测结果
    ├── train/weights/best.pt
    └── detect/
```

## 数据集格式

将数据集放到 `E:\烟草\完整-目标检测--加密--烟草叶部病害`，结构如下：

```
完整-目标检测--加密--烟草叶部病害/
├── images/
│   ├── train/   # 训练图片
│   └── val/     # 验证图片
└── labels/
    ├── train/   # 训练标签 (.txt, YOLO格式)
    └── val/     # 验证标签
```

YOLO 标签格式：每行 `class_id x_center y_center width height`（归一化 0–1）

类别：
- 0: 白星病 (baixingbing)
- 1: 黄叶病 (huayebing)
- 2: 烟青虫 (yanqingchong)
- 3: 叶厚病 (yehuobing)

## 使用步骤

1. 安装依赖：
   ```bash
   pip install -r requirements.txt
   ```

2. 若数据集未划分 train/val，运行：
   ```bash
   python split_dataset.py
   ```

3. 训练：
   ```bash
   python train_yolo.py
   ```

4. 推理：
   ```bash
   python predict_yolo.py test.jpg
   python predict_yolo.py 图片文件夹
   python predict_yolo.py camera
   ```

模型权重保存在 `runs/train/weights/best.pt`。
