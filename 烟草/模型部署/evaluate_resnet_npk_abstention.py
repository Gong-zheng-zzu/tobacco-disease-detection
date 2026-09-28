"""Measure accuracy and coverage when the N/P/K prototype model may abstain."""

import json
import sys
from pathlib import Path

import numpy as np
import torch
from sklearn.metrics import accuracy_score, confusion_matrix
from sklearn.model_selection import LeaveOneGroupOut
from sklearn.neighbors import KNeighborsClassifier
from torchvision.models import ResNet18_Weights, resnet18


sys.path.insert(0, str(Path(__file__).resolve().parent))
from benchmark_resnet_tobacco_npk import features_for
from train_resnet_tobacco_deficiency_experimental import CLASSES, DATA_DIR, load_rows


REPORT = DATA_DIR / "resnet18_abstention_report.json"


def main():
    rows = load_rows()
    labels = np.asarray([CLASSES.index(row["label"]) for row in rows])
    groups = np.asarray([row["source"] for row in rows])
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    model.fc = torch.nn.Identity()
    model.to(device).eval()
    features = features_for(rows, "full_frame", model, device)
    predictions = np.full(len(rows), -1)
    max_vote = np.zeros(len(rows))
    unanimous = np.zeros(len(rows), dtype=bool)
    nearest_distance = np.zeros(len(rows))
    for train, test in LeaveOneGroupOut().split(features, labels, groups):
        mean = features[train].mean(axis=0)
        scale = features[train].std(axis=0)
        scale[scale < 1e-6] = 1
        normalized_train = (features[train] - mean) / scale
        normalized_test = (features[test] - mean) / scale
        head = KNeighborsClassifier(n_neighbors=3, weights="distance")
        head.fit(normalized_train, labels[train])
        predictions[test] = head.predict(normalized_test)
        max_vote[test] = head.predict_proba(normalized_test).max(axis=1)
        distances, neighbors = head.kneighbors(normalized_test)
        nearest_distance[test] = distances[:, 0]
        unanimous[test] = np.all(labels[train][neighbors] == labels[train][neighbors][:, :1], axis=1)

    tiers = []
    for name, selected in [
        ("all", np.ones(len(rows), dtype=bool)),
        ("unanimous_3_neighbors", unanimous),
        ("vote_at_least_0.8", max_vote >= 0.8),
        ("vote_at_least_0.9", max_vote >= 0.9),
    ]:
        tiers.append({
            "rule": name, "answered": int(selected.sum()), "total": len(rows),
            "coverage": float(selected.mean()),
            "accuracy_among_answered": float(accuracy_score(labels[selected], predictions[selected])) if selected.any() else None,
            "class_counts_answered": {name: int(np.sum(selected & (labels == index))) for index, name in enumerate(CLASSES)},
            "confusion_N_P_K": confusion_matrix(labels[selected], predictions[selected], labels=range(3)).tolist() if selected.any() else None,
        })
    report = {
        "validation": "leave-one-publisher-out on 31 source-labeled images",
        "warning": "Thresholds assessed on the same small cohort; not an independent field accuracy estimate. No healthy or other class.",
        "tiers": tiers,
        "images": [
            {"file": row["file"], "source": row["source"], "true_publisher_label": row["label"],
             "prediction": CLASSES[predictions[index]], "max_vote": float(max_vote[index]),
             "unanimous": bool(unanimous[index]), "nearest_distance": float(nearest_distance[index])}
            for index, row in enumerate(rows)
        ],
    }
    REPORT.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(tiers, ensure_ascii=False, indent=2))


if __name__ == "__main__":
    main()
