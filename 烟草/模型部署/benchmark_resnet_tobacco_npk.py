"""Compare conservative ResNet18 heads using leave-one-publisher-out validation."""

import json
import sys
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, recall_score
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.neighbors import KNeighborsClassifier, NearestCentroid
from sklearn.svm import SVC
from torchvision import transforms
from torchvision.models import ResNet18_Weights, resnet18

sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_resnet_tobacco_deficiency_experimental import CLASSES, DATA_DIR, load_rows


REPORT = DATA_DIR / "resnet18_benchmark_report.json"
CHECKPOINT = Path(__file__).resolve().parent / "models" / "resnet18_tobacco_npk_knn_experimental.pth"


def features_for(rows, mode, model, device):
    geometry = ([transforms.Resize(256), transforms.CenterCrop(224)]
                if mode == "center_crop" else [transforms.Resize((224, 224))])
    preprocess = transforms.Compose(geometry + [
        transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    vectors = []
    with torch.inference_mode():
        for row in rows:
            with Image.open(DATA_DIR / row["file"]) as image:
                tensor = preprocess(image.convert("RGB")).unsqueeze(0).to(device)
            vectors.append(model(tensor).cpu().numpy()[0])
    return np.asarray(vectors)


def evaluate(features, labels, groups, method, c=0.1, weight="balanced"):
    predictions = np.full(len(labels), -1)
    for train, test in LeaveOneGroupOut().split(features, labels, groups):
        mean = features[train].mean(axis=0)
        scale = features[train].std(axis=0)
        scale[scale < 1e-6] = 1
        if method == "logistic":
            head = LogisticRegression(C=c, class_weight=weight, max_iter=2000)
        elif method in ("linear_svm", "rbf_svm"):
            head = SVC(C=c, class_weight=weight, kernel="linear" if method == "linear_svm" else "rbf")
        elif method == "centroid":
            head = NearestCentroid()
        else:
            head = KNeighborsClassifier(n_neighbors=int(c), weights="distance")
        head.fit((features[train] - mean) / scale, labels[train])
        predictions[test] = head.predict((features[test] - mean) / scale)
    return {
        "accuracy": float(accuracy_score(labels, predictions)),
        "balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
        "recall_N_P_K": recall_score(labels, predictions, labels=range(3), average=None, zero_division=0).tolist(),
        "confusion_N_P_K": confusion_matrix(labels, predictions, labels=range(3)).tolist(),
    }


def main():
    rows = load_rows()
    labels = np.asarray([CLASSES.index(row["label"]) for row in rows])
    groups = np.asarray([row["source"] for row in rows])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    model.fc = torch.nn.Identity()
    model.to(device).eval()
    variants = []
    feature_sets = {}
    for mode in ("center_crop", "full_frame"):
        features = features_for(rows, mode, model, device)
        feature_sets[mode] = features
        for c in (0.01, 0.1, 1.0, 10.0):
            for weight in ("balanced", None):
                for method in ("logistic", "linear_svm", "rbf_svm"):
                    result = evaluate(features, labels, groups, method, c, weight)
                    variants.append({"preprocess": mode, "method": method, "C": c, "class_weight": weight, **result})
        for method, c in (("centroid", 0), ("knn", 1), ("knn", 3)):
            result = evaluate(features, labels, groups, method, c)
            variants.append({"preprocess": mode, "method": method, "C": c, "class_weight": None, **result})
    baseline = next(v for v in variants if v["preprocess"] == "center_crop" and v["method"] == "logistic" and v["C"] == 0.1 and v["class_weight"] == "balanced")
    best = max(variants, key=lambda item: (item["balanced_accuracy"], item["recall_N_P_K"][1], item["accuracy"]))
    best_with_phosphorus = max((v for v in variants if v["recall_N_P_K"][1] > 0), key=lambda item: (item["balanced_accuracy"], item["accuracy"]), default=None)
    report = {
        "note": "Exploratory model selection on the same small cross-source folds; scores after selection are optimistic.",
        "image_count": len(rows), "baseline": baseline, "best": best,
        "best_with_phosphorus_recall": best_with_phosphorus, "variants": variants,
    }
    if best["method"] == "knn":
        features = feature_sets[best["preprocess"]]
        mean = features.mean(axis=0)
        scale = features.std(axis=0)
        scale[scale < 1e-6] = 1
        CHECKPOINT.parent.mkdir(parents=True, exist_ok=True)
        torch.save({
            "backbone_state_dict": model.cpu().state_dict(),
            "class_names": CLASSES,
            "feature_mean": torch.from_numpy(mean),
            "feature_scale": torch.from_numpy(scale),
            "reference_features": torch.from_numpy((features - mean) / scale),
            "reference_labels": torch.from_numpy(labels),
            "reference_files": [row["file"] for row in rows],
            "neighbors": int(best["C"]),
            "preprocess": best["preprocess"],
            "status": "experimental_research_only_not_validated_for_field_use",
        }, CHECKPOINT)
        report["experimental_checkpoint"] = str(CHECKPOINT)
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps({"baseline": baseline, "best": best, "best_with_phosphorus_recall": best_with_phosphorus}, ensure_ascii=False, indent=2), flush=True)


if __name__ == "__main__":
    main()
