"""Train an experimental N/P/K tobacco classifier from reviewed web candidates."""

import csv
import json
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix
from sklearn.model_selection import LeaveOneGroupOut
from torchvision import transforms
from torchvision.models import ResNet18_Weights, resnet18


ROOT = Path(__file__).resolve().parents[1]
DATA_DIR = ROOT / "tobacco_deficiency_candidates"
OUTPUT = ROOT / "模型部署" / "models" / "resnet18_tobacco_npk_experimental.pth"
REPORT = DATA_DIR / "resnet18_experiment_report.json"
CLASSES = ["N", "P", "K"]

# Mixed-class comparisons, montages and distant field views have no valid whole-image label.
EXCLUDED = {
    "N/ncsu_N_01.jpg": "deficient and control plants together",
    "N/ncsu_N_04.jpg": "distant field view",
    "N/ncsu_N_05.jpg": "distant field view",
    "P/ncsu_P_01.jpg": "deficient and control plants together",
    "P/ncsu_P_04.jpg": "multiple seedlings",
    "P/ncsu_P_05.gif": "captioned montage",
    "K/ncsu_K_02.jpg": "deficient and control plants together",
    "K/ncsu_K_05.gif": "captioned montage",
    "K/ncsu_K_06.jpg": "distant field view",
    "K/ncsu_K_08.jpg": "distant field view",
    "K/uky_K_02.jpg": "distant field view",
}


def load_rows():
    with (DATA_DIR / "manifest.csv").open(encoding="utf-8-sig", newline="") as stream:
        rows = list(csv.DictReader(stream))
    selected = [row for row in rows if row["file"] not in EXCLUDED]
    if len(selected) < 20 or set(row["label"] for row in selected) != set(CLASSES):
        raise ValueError("Insufficient N/P/K candidates")
    for row in selected:
        if not (DATA_DIR / row["file"]).is_file():
            raise FileNotFoundError(row["file"])
    return selected


def extract_features(rows):
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    model.fc = torch.nn.Identity()
    model.to(device).eval()
    preprocess = transforms.Compose([
        transforms.Resize(256), transforms.CenterCrop(224), transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    features = []
    with torch.inference_mode():
        for row in rows:
            with Image.open(DATA_DIR / row["file"]) as image:
                tensor = preprocess(image.convert("RGB")).unsqueeze(0).to(device)
            features.append(model(tensor).cpu().numpy()[0])
    print(f"Extracted {len(features)} ResNet18 features on {device}", flush=True)
    return np.asarray(features), model


def train_head(features, labels):
    mean = features.mean(axis=0)
    scale = features.std(axis=0)
    scale[scale < 1e-6] = 1
    classifier = LogisticRegression(C=0.1, class_weight="balanced", max_iter=2000)
    classifier.fit((features - mean) / scale, labels)
    return classifier, mean, scale


def main():
    rows = load_rows()
    features, backbone = extract_features(rows)
    labels = np.asarray([CLASSES.index(row["label"]) for row in rows])
    groups = np.asarray([row["source"] for row in rows])
    predictions = np.full(len(rows), -1)
    fold_reports = []
    for train_indices, test_indices in LeaveOneGroupOut().split(features, labels, groups):
        head, mean, scale = train_head(features[train_indices], labels[train_indices])
        predicted = head.predict((features[test_indices] - mean) / scale)
        predictions[test_indices] = predicted
        fold_reports.append({
            "held_out_source": str(groups[test_indices[0]]),
            "sample_count": int(len(test_indices)),
            "accuracy": float(accuracy_score(labels[test_indices], predicted)),
            "class_counts": dict(Counter(rows[i]["label"] for i in test_indices)),
        })
    if np.any(predictions < 0):
        raise RuntimeError("Some images were not evaluated")

    head, mean, scale = train_head(features, labels)
    # Fold feature standardization into the final linear layer for ordinary ResNet inference.
    weight = head.coef_ / scale
    bias = head.intercept_ - weight @ mean
    backbone.fc = torch.nn.Linear(features.shape[1], len(CLASSES))
    backbone.fc.weight.data.copy_(torch.from_numpy(weight).float())
    backbone.fc.bias.data.copy_(torch.from_numpy(bias).float())
    OUTPUT.parent.mkdir(parents=True, exist_ok=True)
    torch.save({
        "model_state_dict": backbone.cpu().state_dict(),
        "class_names": CLASSES,
        "training_image_count": len(rows),
        "status": "experimental_research_only_not_validated_for_field_use",
    }, OUTPUT)

    report = {
        "purpose": "Experimental tobacco N/P/K image classification; no healthy class",
        "source_labeled_images": len(rows) + len(EXCLUDED),
        "excluded_images": EXCLUDED,
        "training_images": len(rows),
        "class_counts": dict(Counter(row["label"] for row in rows)),
        "source_counts": dict(Counter(row["source"] for row in rows)),
        "validation": "leave-one-publisher-out; final checkpoint retrained on all selected images",
        "cross_source_accuracy": float(accuracy_score(labels, predictions)),
        "cross_source_balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
        "confusion_matrix_rows_true_columns_predicted_N_P_K": confusion_matrix(labels, predictions, labels=range(3)).tolist(),
        "folds": fold_reports,
        "checkpoint": str(OUTPUT),
        "limitations": "Publisher labels and reuse rights unverified; small sample; no healthy class; no independent tobacco field test",
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(report, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
