"""
烟草叶部病害目标检测 - YOLOv8 推理脚本
支持: 单图 / 文件夹 / 摄像头
"""
import os
import sys
from pathlib import Path

try:
    from ultralytics import YOLO
    import cv2
except ImportError as e:
    print("请先安装: pip install ultralytics opencv-python")
    sys.exit(1)

SCRIPT_DIR = Path(__file__).resolve().parent
# 与 Django 后端 drf_test002/model_weights 共用权重（训练完成可复制为 yolov8n_best.pt）
DRF_YOLO_WEIGHTS = SCRIPT_DIR.parent / "前后端" / "drf_test002" / "model_weights" / "yolov8n_best.pt"
LEGACY_WEIGHTS = SCRIPT_DIR / "runs" / "train" / "weights" / "best.pt"
WEIGHTS = DRF_YOLO_WEIGHTS if DRF_YOLO_WEIGHTS.is_file() else LEGACY_WEIGHTS
# 英文类名 -> 中文类名
CLASS_TO_CN = {
    "baixingbing": "白星病",
    "huayebing": "黄叶病",
    "yanqingchong": "烟青虫",
    "yehuobing": "叶厚病",
}

# 默认输入/输出目录
INPUT_DIR = SCRIPT_DIR / "test"
OUTPUT_DIR = SCRIPT_DIR / "result"
IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def get_image_paths(dir_path):
    """只收集目录中的图片文件"""
    dir_path = Path(dir_path)
    if not dir_path.is_dir():
        return []
    return sorted([p for p in dir_path.iterdir() if p.suffix.lower() in IMAGE_EXTENSIONS])


def get_detected_chinese_suffix(model, result):
    """根据检测结果得到中文类型后缀，如 _白星病_烟青虫"""
    if result.boxes is None or len(result.boxes) == 0:
        return "_未检出"
    cls_ids = result.boxes.cls.int().tolist()
    names = model.names or {}
    # 去重并按类别顺序排列（0,1,2,3 -> 白星病、黄叶病、烟青虫、叶厚病）
    unique_ids = sorted(set(cls_ids))
    cn_parts = [CLASS_TO_CN.get(names.get(i, ""), str(i)) for i in unique_ids if i in names]
    if not cn_parts:
        return "_未检出"
    return "_" + "_".join(cn_parts)


def predict_image(model, source, save_dir=None):
    """对图片或目录进行预测，只处理图片文件，输出图片重命名为「原名_中文类型」"""
    source = Path(source)
    if source.is_dir():
        image_paths = get_image_paths(source)
        if not image_paths:
            print(f"目录中无图片: {source}")
            return []
        sources = image_paths
    else:
        sources = [Path(source)]

    OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
    results = model.predict(
        source=[str(p) for p in sources],
        save=False,
        verbose=True,
    )

    for path, result in zip(sources, results):
        stem, ext = path.stem, path.suffix
        suffix = get_detected_chinese_suffix(model, result)
        new_name = f"{stem}{suffix}{ext}"
        out_path = OUTPUT_DIR / new_name
        # 画框并保存（避免中文路径/文件名问题用 imencode）
        ann = result.plot()
        ann_bgr = cv2.cvtColor(ann, cv2.COLOR_RGB2BGR)
        ok, buf = cv2.imencode(ext if ext.lower() in (".jpg", ".jpeg", ".png") else ".jpg", ann_bgr)
        if ok:
            with open(out_path, "wb") as f:
                f.write(buf.tobytes())
            print(f"  保存: {new_name}")

    return results


def predict_camera(model):
    """从摄像头实时检测"""
    cap = cv2.VideoCapture(0)
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    print("按 q 退出")
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        results = model.predict(frame, verbose=False)
        ann = results[0].plot()
        cv2.imshow("烟草病害检测", ann)
        if cv2.waitKey(1) & 0xFF == ord("q"):
            break
    cap.release()
    cv2.destroyAllWindows()


def main():
    # 优先使用训练好的 best.pt，若无则用预训练 yolov8n
    if WEIGHTS.exists():
        model = YOLO(str(WEIGHTS))
        print(f"加载模型: {WEIGHTS}")
    else:
        model = YOLO("yolov8n.pt")
        print("未找到 best.pt，使用预训练 yolov8n.pt 作为演示")

    if len(sys.argv) > 1:
        arg = sys.argv[1]
        if arg == "camera" or arg == "0":
            predict_camera(model)
        elif os.path.isfile(arg):
            predict_image(model, arg)
        elif os.path.isdir(arg):
            predict_image(model, arg)
        else:
            print("用法: python predict_yolo.py [图片路径|目录|camera]")
    else:
        # 默认：输入 E:\烟草\disease\test，输出 E:\烟草\disease\result，只处理图片
        OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
        if INPUT_DIR.exists():
            predict_image(model, INPUT_DIR)
            print(f"结果已保存到: {OUTPUT_DIR}")
        else:
            print(f"输入目录不存在: {INPUT_DIR}")
            print("用法: python predict_yolo.py [图片路径|目录|camera]")


if __name__ == "__main__":
    main()
