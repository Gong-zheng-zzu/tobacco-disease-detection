"""Run the research-only tobacco N/P/K nearest-neighbor classifier."""

import argparse
from pathlib import Path

import torch
from PIL import Image
from torchvision import transforms
from torchvision.models import resnet18


DEFAULT_CHECKPOINT = Path(__file__).resolve().parent / "models" / "resnet18_tobacco_npk_knn_experimental.pth"


def predict(image_path, checkpoint_path=DEFAULT_CHECKPOINT):
    checkpoint = torch.load(checkpoint_path, map_location="cpu", weights_only=True)
    if checkpoint["preprocess"] != "full_frame":
        raise ValueError("Unsupported preprocessing mode")
    model = resnet18(weights=None)
    model.fc = torch.nn.Identity()
    model.load_state_dict(checkpoint["backbone_state_dict"])
    model.eval()
    preprocess = transforms.Compose([
        transforms.Resize((224, 224)), transforms.ToTensor(),
        transforms.Normalize([0.485, 0.456, 0.406], [0.229, 0.224, 0.225]),
    ])
    with Image.open(image_path) as image, torch.inference_mode():
        feature = model(preprocess(image.convert("RGB")).unsqueeze(0))[0]
    feature = (feature - checkpoint["feature_mean"]) / checkpoint["feature_scale"]
    distances = torch.linalg.vector_norm(checkpoint["reference_features"] - feature, dim=1)
    indices = distances.topk(checkpoint["neighbors"], largest=False).indices
    labels = checkpoint["reference_labels"][indices].long()
    if torch.any(distances[indices] == 0):
        votes = torch.bincount(labels[distances[indices] == 0], minlength=len(checkpoint["class_names"]))
    else:
        votes = torch.zeros(len(checkpoint["class_names"]))
        votes.scatter_add_(0, labels, 1 / distances[indices])
    prediction = checkpoint["class_names"][votes.argmax().item()]
    neighbors = [checkpoint["reference_files"][index] for index in indices.tolist()]
    return prediction, neighbors


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("image", type=Path)
    parser.add_argument("--checkpoint", type=Path, default=DEFAULT_CHECKPOINT)
    args = parser.parse_args()
    label, neighbors = predict(args.image, args.checkpoint)
    print(f"Experimental label: {label} (not a field diagnosis)")
    print("Nearest references: " + ", ".join(neighbors))


if __name__ == "__main__":
    main()
