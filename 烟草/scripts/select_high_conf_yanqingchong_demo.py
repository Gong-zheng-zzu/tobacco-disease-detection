"""Select a real, labeled tobacco smoke-worm image for the demo gallery."""
from __future__ import annotations

import argparse
import csv
import shutil
from pathlib import Path

from ultralytics import YOLO


def main() -> None:
    parser = argparse.ArgumentParser()
    parser.add_argument("--dataset", type=Path, default=Path("烟草/unified_tobacco_dataset"))
    parser.add_argument("--weights", type=Path, default=Path("烟草/前后端/drf_test002/model_weights/yolo_unified_6class_best.pt"))
    parser.add_argument("--output", type=Path, default=Path("烟草/1/app/true/tobacco/public/demo-images/烟青虫_1.jpg"))
    parser.add_argument("--report", type=Path, default=Path("烟草/docs/training_results/yanqingchong_demo_selection.csv"))
    args = parser.parse_args()

    image_dir = args.dataset / "images" / "test"
    label_dir = args.dataset / "labels" / "test"
    model = YOLO(str(args.weights))
    candidates = []
    for label_path in sorted(label_dir.glob("*.txt")):
        if not any(line.split(maxsplit=1)[0] == "2" for line in label_path.read_text(encoding="utf-8").splitlines() if line.strip()):
            continue
        image = next((image_dir / f"{label_path.stem}{ext}" for ext in (".jpg", ".JPG", ".jpeg", ".JPEG", ".png") if (image_dir / f"{label_path.stem}{ext}").exists()), None)
        if image is None:
            continue
        result = model.predict(str(image), imgsz=640, conf=0.05, augment=True, verbose=False)[0]
        scores = [float(score) for cls, score in zip(result.boxes.cls, result.boxes.conf) if int(cls) == 2]
        other_scores = [float(score) for cls, score in zip(result.boxes.cls, result.boxes.conf) if int(cls) != 2]
        if scores:
            candidates.append((max(scores), max(other_scores, default=0.0), image))

    candidates.sort(key=lambda item: (item[1] < 0.5, item[0]), reverse=True)
    if not candidates:
        raise SystemExit("No labeled yanqingchong candidates found")
    args.output.parent.mkdir(parents=True, exist_ok=True)
    shutil.copy2(candidates[0][2], args.output)
    args.report.parent.mkdir(parents=True, exist_ok=True)
    with args.report.open("w", newline="", encoding="utf-8") as handle:
        writer = csv.writer(handle)
        writer.writerow(("rank", "file", "model_score", "other_max_score", "source_label"))
        for rank, (score, other_score, image) in enumerate(candidates[:20], 1):
            writer.writerow((rank, str(image), f"{score:.6f}", f"other_max={other_score:.6f}", "class_id_2_yanqingchong"))
    print(f"selected={candidates[0][2]} score={candidates[0][0]:.6f} other_max={candidates[0][1]:.6f} output={args.output}")


if __name__ == "__main__":
    main()
