"""Rank new tobacco photos for human N/P/K/healthy/other labeling.

The experimental model proposes a review order, never a training label.
"""

import argparse
import csv
from pathlib import Path

import numpy as np
import torch
from PIL import Image, ImageDraw, ImageOps
from torchvision import transforms
from torchvision.models import resnet18


CHECKPOINT = Path(__file__).resolve().parent / "models" / "resnet18_tobacco_npk_knn_experimental.pth"
EXTENSIONS = {".jpg", ".jpeg", ".png", ".webp"}


def load_model():
    checkpoint = torch.load(CHECKPOINT, map_location="cpu", weights_only=True)
    model = resnet18(weights=None)
    model.fc = torch.nn.Identity()
    model.load_state_dict(checkpoint["backbone_state_dict"])
    model.eval()
    preprocess = transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    return checkpoint, model, preprocess


def describe_image(path, checkpoint, model, preprocess):
    with Image.open(path) as image, torch.inference_mode():
        vector = model(preprocess(image.convert("RGB")).unsqueeze(0))[0]
    vector = (vector - checkpoint["feature_mean"]) / checkpoint["feature_scale"]
    distances = torch.linalg.vector_norm(checkpoint["reference_features"] - vector, dim=1)
    indices = distances.topk(checkpoint["neighbors"], largest=False).indices
    labels = checkpoint["reference_labels"][indices].long()
    votes = torch.zeros(len(checkpoint["class_names"]))
    if torch.any(distances[indices] == 0):
        votes.scatter_add_(0, labels[distances[indices] == 0], torch.ones_like(labels[distances[indices] == 0], dtype=torch.float32))
    else:
        votes.scatter_add_(0, labels, 1 / distances[indices])
    scores = votes / votes.sum()
    top = scores.argsort(descending=True)
    margin = (scores[top[0]] - scores[top[1]]).item()
    return {
        "path": str(path.resolve()),
        "proposed_label_not_verified": checkpoint["class_names"][top[0]],
        "vote_margin_not_probability": round(margin, 4),
        "nearest_distance": round(distances[indices[0]].item(), 4),
        "nearest_reference": checkpoint["reference_files"][indices[0]],
        "pk_ambiguous": set(top[:2].tolist()) == {1, 2},
        "review_label_N_P_K_healthy_other": "",
        "review_notes": "",
        "_vector": vector.numpy(),
    }


def select_diverse(rows, limit):
    # First prioritize uncertain P/K cases, then spread selected samples in feature space.
    rows.sort(key=lambda row: (not row["pk_ambiguous"], row["vote_margin_not_probability"]))
    pool = rows[: max(limit * 5, limit)]
    selected = []
    while pool and len(selected) < limit:
        if not selected:
            chosen = pool.pop(0)
        else:
            best_index = max(range(len(pool)), key=lambda index: min(np.linalg.norm(pool[index]["_vector"] - item["_vector"]) for item in selected))
            chosen = pool.pop(best_index)
        selected.append(chosen)
    return selected


def write_contact_sheet(rows, output):
    width, height, columns = 200, 160, 5
    sheet = Image.new("RGB", (width * columns, height * ((len(rows) + columns - 1) // columns)), "white")
    draw = ImageDraw.Draw(sheet)
    for index, row in enumerate(rows):
        with Image.open(row["path"]) as image:
            preview = ImageOps.contain(image.convert("RGB"), (width - 8, height - 32))
        x, y = index % columns * width, index // columns * height
        sheet.paste(preview, (x + 4, y + 4))
        draw.text((x + 4, y + height - 25), f"{index + 1}. {Path(row['path']).name[:22]}", fill="black")
    sheet.save(output)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("input_dir", type=Path, help="Directory of new, unlabelled tobacco photos")
    parser.add_argument("output_dir", type=Path)
    parser.add_argument("--limit", type=int, default=30)
    args = parser.parse_args()
    paths = sorted(path for path in args.input_dir.rglob("*") if path.suffix.lower() in EXTENSIONS)
    if not paths:
        raise ValueError("No photos found")
    checkpoint, model, preprocess = load_model()
    rows = []
    for path in paths:
        try:
            rows.append(describe_image(path, checkpoint, model, preprocess))
        except (OSError, ValueError) as exc:
            print(f"Skipped {path}: {exc}")
    selected = select_diverse(rows, max(1, args.limit))
    args.output_dir.mkdir(parents=True, exist_ok=True)
    fields = [key for key in selected[0] if key != "_vector"]
    with (args.output_dir / "review_queue.csv").open("w", newline="", encoding="utf-8-sig") as stream:
        writer = csv.DictWriter(stream, fieldnames=fields)
        writer.writeheader()
        writer.writerows({key: row[key] for key in fields} for row in selected)
    write_contact_sheet(selected, args.output_dir / "review_contact_sheet.jpg")
    print(f"Selected {len(selected)} of {len(rows)} photos for human review: {args.output_dir}")


if __name__ == "__main__":
    main()
