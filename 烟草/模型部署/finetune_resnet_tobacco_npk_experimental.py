"""Fixed-recipe ResNet18 fine-tuning with publisher-held-out evaluation."""

import json
import sys
from collections import Counter
from pathlib import Path

import numpy as np
import torch
from PIL import Image
from sklearn.metrics import accuracy_score, balanced_accuracy_score, confusion_matrix, recall_score
from sklearn.model_selection import LeaveOneGroupOut
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import ResNet18_Weights, resnet18


sys.path.insert(0, str(Path(__file__).resolve().parent))
from train_resnet_tobacco_deficiency_experimental import CLASSES, DATA_DIR, load_rows


REPORT = DATA_DIR / "resnet18_finetune_report.json"
EPOCHS = 100
SEED = 42


class Samples(Dataset):
    def __init__(self, rows, indices, transform):
        self.rows = [rows[i] for i in indices]
        self.transform = transform

    def __len__(self):
        return len(self.rows)

    def __getitem__(self, index):
        row = self.rows[index]
        with Image.open(DATA_DIR / row["file"]) as image:
            return self.transform(image.convert("RGB")), CLASSES.index(row["label"])


def build_model(device):
    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, len(CLASSES))
    for parameter in model.parameters():
        parameter.requires_grad = False
    for parameter in model.layer4.parameters():
        parameter.requires_grad = True
    for parameter in model.fc.parameters():
        parameter.requires_grad = True
    return model.to(device)


def evaluate(model, loader, device):
    model.eval()
    predictions = []
    with torch.inference_mode():
        for images, _ in loader:
            predictions.extend(model(images.to(device)).argmax(1).cpu().tolist())
    return predictions


def main():
    torch.manual_seed(SEED)
    np.random.seed(SEED)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    rows = load_rows()
    labels = np.asarray([CLASSES.index(row["label"]) for row in rows])
    groups = np.asarray([row["source"] for row in rows])
    normalize = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    train_transform = transforms.Compose([
        transforms.Resize((224, 224)), transforms.RandomHorizontalFlip(),
        transforms.ColorJitter(brightness=0.12, contrast=0.12, saturation=0.08),
        transforms.ToTensor(), normalize,
    ])
    eval_transform = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(), normalize])
    predictions_by_epoch = np.full((EPOCHS, len(rows)), -1)
    train_correct_by_epoch = np.zeros(EPOCHS, dtype=np.int64)
    train_total_by_epoch = np.zeros(EPOCHS, dtype=np.int64)
    folds = []
    for train_indices, test_indices in LeaveOneGroupOut().split(np.zeros(len(rows)), labels, groups):
        torch.manual_seed(SEED)
        model = build_model(device)
        counts = np.bincount(labels[train_indices], minlength=len(CLASSES))
        weights = len(train_indices) / (len(CLASSES) * counts)
        loss_fn = nn.CrossEntropyLoss(weight=torch.tensor(weights, dtype=torch.float32, device=device))
        optimizer = torch.optim.AdamW([
            {"params": model.layer4.parameters(), "lr": 1e-5},
            {"params": model.fc.parameters(), "lr": 5e-4},
        ], weight_decay=1e-4)
        train_loader = DataLoader(Samples(rows, train_indices, train_transform), batch_size=4, shuffle=True)
        train_eval_loader = DataLoader(Samples(rows, train_indices, eval_transform), batch_size=4)
        test_loader = DataLoader(Samples(rows, test_indices, eval_transform), batch_size=4)
        fold_accuracy_by_epoch = []
        for epoch in range(EPOCHS):
            model.train()
            for module in model.modules():
                if isinstance(module, nn.BatchNorm2d):
                    module.eval()
            for images, targets in train_loader:
                optimizer.zero_grad(set_to_none=True)
                loss = loss_fn(model(images.to(device)), targets.to(device))
                loss.backward()
                optimizer.step()
            predicted = evaluate(model, test_loader, device)
            predictions_by_epoch[epoch, test_indices] = predicted
            fold_accuracy_by_epoch.append(float(accuracy_score(labels[test_indices], predicted)))
            train_predicted = evaluate(model, train_eval_loader, device)
            train_correct_by_epoch[epoch] += np.sum(labels[train_indices] == train_predicted)
            train_total_by_epoch[epoch] += len(train_indices)
        folds.append({
            "source": str(groups[test_indices[0]]), "count": len(test_indices),
            "accuracy_by_epoch": fold_accuracy_by_epoch,
            "class_counts": dict(Counter(rows[i]["label"] for i in test_indices)),
        })
        print(f"Held out {folds[-1]['source']}: epoch 1={fold_accuracy_by_epoch[0]:.3f}, epoch {EPOCHS}={fold_accuracy_by_epoch[-1]:.3f}", flush=True)
        del model, optimizer
        if device.type == "cuda":
            torch.cuda.empty_cache()
    epoch_results = []
    for epoch, predictions in enumerate(predictions_by_epoch, 1):
        epoch_results.append({
            "epoch": epoch,
            "train_accuracy": float(train_correct_by_epoch[epoch - 1] / train_total_by_epoch[epoch - 1]),
            "accuracy": float(accuracy_score(labels, predictions)),
            "balanced_accuracy": float(balanced_accuracy_score(labels, predictions)),
            "recall_N_P_K": recall_score(labels, predictions, labels=range(3), average=None, zero_division=0).tolist(),
            "confusion_N_P_K": confusion_matrix(labels, predictions, labels=range(3)).tolist(),
        })
    result = {
        "recipe": "100 epochs; pretrained ResNet18; train layer4 and fc; class-weighted loss; BN frozen",
        "validation": "leave-one-publisher-out; epoch sweep is exploratory model selection on the same folds",
        "image_count": len(rows), "class_counts": dict(Counter(row["label"] for row in rows)),
        "epochs": epoch_results,
        "folds": folds,
    }
    REPORT.write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")
    best = max(epoch_results, key=lambda item: item["accuracy"])
    print(json.dumps({"epoch_count": EPOCHS, "best": best, "last": epoch_results[-1]}, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
