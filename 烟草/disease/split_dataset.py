"""
将烟草病害数据集按 8:2 划分为 train/val
若数据集未划分，运行此脚本自动创建 images/train、images/val、labels/train、labels/val
"""
import os
import shutil
import random
from pathlib import Path

SCRIPT_DIR = Path(__file__).resolve().parent
# 数据集根目录（与 data.yaml 中的 path 一致）
DATASET_ROOT = Path(r"E:\烟草\完整-目标检测--加密--烟草叶部病害")
TRAIN_RATIO = 0.8
RANDOM_SEED = 42


def find_images_and_labels(root: Path):
    """查找 images 和 labels 目录（支持多种常见结构）"""
    root = Path(root)
    if not root.exists():
        return None, None

    # 结构1: images/ + labels/
    img_dir = root / "images"
    lbl_dir = root / "labels"
    if img_dir.exists() and lbl_dir.exists():
        return img_dir, lbl_dir

    # 结构2: 根目录下直接有图片和同名txt
    imgs = list(root.glob("*.jpg")) + list(root.glob("*.png")) + list(root.glob("*.jpeg"))
    lbls = list(root.glob("*.txt"))
    if imgs:
        return root, root

    # 结构3: all_images/ + all_txt/
    all_img = root / "all_images"
    all_txt = root / "all_txt"
    if all_img.exists() and all_txt.exists():
        return all_img, all_txt

    # 结构4: 子目录 train/val 已存在
    tr_img = root / "images" / "train"
    tr_lbl = root / "labels" / "train"
    if tr_img.exists() and tr_lbl.exists():
        print("数据集已划分，无需执行 split_dataset.py")
        return None, None

    return None, None


def split_dataset(img_dir: Path, lbl_dir: Path):
    out_root = DATASET_ROOT
    out_img_train = out_root / "images" / "train"
    out_img_val = out_root / "images" / "val"
    out_lbl_train = out_root / "labels" / "train"
    out_lbl_val = out_root / "labels" / "val"

    for d in [out_img_train, out_img_val, out_lbl_train, out_lbl_val]:
        d.mkdir(parents=True, exist_ok=True)

    exts = {".jpg", ".jpeg", ".png"}
    pairs = []
    src_img = Path(img_dir)
    src_lbl = Path(lbl_dir)

    for f in src_img.iterdir() if src_img.is_dir() else [src_img]:
        if f.suffix.lower() not in exts:
            continue
        stem = f.stem
        lbl_file = src_lbl / f"{stem}.txt"
        if lbl_file.exists():
            pairs.append((f, lbl_file))

    random.seed(RANDOM_SEED)
    random.shuffle(pairs)
    n = len(pairs)
    n_train = int(n * TRAIN_RATIO)

    for i, (img_path, lbl_path) in enumerate(pairs):
        if i < n_train:
            dst_img, dst_lbl = out_img_train, out_lbl_train
        else:
            dst_img, dst_lbl = out_img_val, out_lbl_val
        shutil.copy2(img_path, dst_img / img_path.name)
        shutil.copy2(lbl_path, dst_lbl / lbl_path.name)

    print(f"划分完成: train={n_train}, val={n - n_train}")


def main():
    if not DATASET_ROOT.exists():
        print(f"数据集目录不存在: {DATASET_ROOT}")
        print("请将 完整-目标检测--加密--烟草叶部病害 数据集放到该路径，或修改本脚本中的 DATASET_ROOT")
        return

    img_dir, lbl_dir = find_images_and_labels(DATASET_ROOT)
    if img_dir is None or lbl_dir is None:
        print("未找到有效的 images/labels 结构，请手动按 YOLO 格式组织数据集:")
        print("  path/")
        print("    images/")
        print("      train/  (或 根目录)")
        print("      val/")
        print("    labels/")
        print("      train/")
        print("      val/")
        return

    split_dataset(img_dir, lbl_dir)


if __name__ == "__main__":
    main()
