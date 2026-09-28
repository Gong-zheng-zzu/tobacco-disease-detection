"""Train a healthy / potassium-deficiency ResNet18 with a held-out test set."""

import argparse
import random
from pathlib import Path

import torch
from PIL import Image
from torch import nn
from torch.utils.data import DataLoader, Dataset
from torchvision import transforms
from torchvision.models import ResNet18_Weights, resnet18


ROOT = Path(__file__).resolve().parents[1]
DATA_ROOT = ROOT / "模型部署数据集"
DEFAULT_OUTPUT = ROOT / "模型部署" / "models" / "model_resnet18_retrained_k.pth"
SUFFIXES = ("_blur", "_brighter", "_darker", "_fli", "_noise", "_masked", "_r180", "_r90")
SOURCES = (
    ("healthy_validation_set", 0, "development"),
    ("缺磷数据预处理_validation_set", 1, "development"),
    ("healthy_test_set", 0, "test"),
    ("缺磷数据预处理_test_set", 1, "test"),
)


def base_name(path):
    stem = path.stem
    for suffix in SUFFIXES:
        if stem.endswith(suffix):
            return stem[: -len(suffix)]
    return stem


def collect_samples():
    samples = {"development": {0: {}, 1: {}}, "test": {0: {}, 1: {}}}
    for dirname, label, split in SOURCES:
        files = sorted(path for path in (DATA_ROOT / dirname).rglob("*") if path.suffix.lower() in {".jpg", ".jpeg", ".png"})
        if not files:
            raise ValueError(f"No images found in {DATA_ROOT / dirname}")
        if label == 1 and any(not path.stem.startswith("potassium_deficiency_") for path in files):
            raise ValueError(f"Unexpected deficiency label in {dirname}")
        for path in files:
            samples[split][label].setdefault(base_name(path), []).append(path)
    for label in (0, 1):
        overlap = samples["development"][label].keys() & samples["test"][label].keys()
        if overlap:
            raise ValueError(f"Development/test overlap for class {label}: {sorted(overlap)[:3]}")
    return samples


def split_samples(samples, seed):
    rng = random.Random(seed)
    train, val, test = [], [], []
    for label in (0, 1):
        groups = list(samples["development"][label].items())
        rng.shuffle(groups)
        val_count = max(1, round(len(groups) * 0.2))
        for _, paths in groups[:val_count]:
            val.append((next((p for p in paths if p.stem == base_name(p)), paths[0]), label))
        for _, paths in groups[val_count:]:
            train.extend((path, label) for path in paths)
        for _, paths in samples["test"][label].items():
            test.append((next((p for p in paths if p.stem == base_name(p)), paths[0]), label))
    return train, val, test


class LeafDataset(Dataset):
    def __init__(self, samples, transform):
        self.samples = samples
        self.transform = transform

    def __len__(self):
        return len(self.samples)

    def __getitem__(self, index):
        path, label = self.samples[index]
        with Image.open(path) as image:
            return self.transform(image.convert("RGB")), label


def evaluate(model, loader, device):
    model.eval()
    correct = total = 0
    confusion = [[0, 0], [0, 0]]
    with torch.inference_mode():
        for images, labels in loader:
            prediction = model(images.to(device)).argmax(1).cpu()
            for expected, actual in zip(labels.tolist(), prediction.tolist()):
                confusion[expected][actual] += 1
                correct += expected == actual
                total += 1
    return correct / total, confusion


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--epochs", type=int, default=12)
    parser.add_argument("--batch-size", type=int, default=16)
    parser.add_argument("--seed", type=int, default=42)
    parser.add_argument("--output", type=Path, default=DEFAULT_OUTPUT)
    args = parser.parse_args()
    torch.manual_seed(args.seed)
    if torch.cuda.is_available():
        torch.cuda.manual_seed_all(args.seed)
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")

    train, val, test = split_samples(collect_samples(), args.seed)
    normalize = transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225])
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)), transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(), transforms.ColorJitter(0.2, 0.2, 0.2),
        transforms.ToTensor(), normalize,
    ])
    eval_transform = transforms.Compose([transforms.Resize((224, 224)), transforms.ToTensor(), normalize])
    train_loader = DataLoader(LeafDataset(train, train_transform), batch_size=args.batch_size, shuffle=True, num_workers=0)
    val_loader = DataLoader(LeafDataset(val, eval_transform), batch_size=args.batch_size, num_workers=0)
    test_loader = DataLoader(LeafDataset(test, eval_transform), batch_size=args.batch_size, num_workers=0)
    print(f"Device: {device}; train={len(train)}, val={len(val)}, test={len(test)}", flush=True)

    model = resnet18(weights=ResNet18_Weights.IMAGENET1K_V1)
    model.fc = nn.Linear(model.fc.in_features, 2)
    model.to(device)
    optimizer = torch.optim.AdamW(model.parameters(), lr=1e-4, weight_decay=1e-4)
    criterion = nn.CrossEntropyLoss()
    best_accuracy = -1.0
    patience = 0
    args.output.parent.mkdir(parents=True, exist_ok=True)
    for epoch in range(args.epochs):
        model.train()
        for images, labels in train_loader:
            optimizer.zero_grad(set_to_none=True)
            loss = criterion(model(images.to(device)), labels.to(device))
            loss.backward()
            optimizer.step()
        accuracy, _ = evaluate(model, val_loader, device)
        print(f"Epoch {epoch + 1}: val_accuracy={accuracy:.4f}", flush=True)
        if accuracy > best_accuracy:
            best_accuracy = accuracy
            torch.save(model.state_dict(), args.output)
            patience = 0
        else:
            patience += 1
            if patience >= 4:
                break

    model.load_state_dict(torch.load(args.output, map_location=device, weights_only=True))
    accuracy, confusion = evaluate(model, test_loader, device)
    print(f"Held-out test accuracy={accuracy:.4f}; confusion_matrix={confusion}", flush=True)
    print(f"Saved: {args.output}", flush=True)


if __name__ == "__main__":
    main()
