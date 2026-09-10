"""评估 ResNet18 模型准确度"""
import torch
import torch.nn as nn
from torchvision import datasets, transforms
from torchvision.models import resnet18
from torch.utils.data import DataLoader, ConcatDataset
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "模型部署数据集")
MODEL_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "前后端", "drf_test002", "model_weights", "model_resnet18.pth")
)
if not os.path.isfile(MODEL_PATH):
    MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "model_resnet18.pth")


class RemapLabelDataset(torch.utils.data.Dataset):
    def __init__(self, dataset, label_offset=0):
        self.dataset = dataset
        self.offset = label_offset

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        img, lbl = self.dataset[idx]
        return img, lbl + self.offset


transform = transforms.Compose([
    transforms.Resize((224, 224)),
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

val_health = datasets.ImageFolder(os.path.join(DATA_DIR, "healthy_validation_set"), transform=transform)
test_health = datasets.ImageFolder(os.path.join(DATA_DIR, "healthy_test_set"), transform=transform)
val_def = RemapLabelDataset(
    datasets.ImageFolder(os.path.join(DATA_DIR, "缺磷数据预处理_validation_set"), transform=transform),
    label_offset=1,
)
test_def = RemapLabelDataset(
    datasets.ImageFolder(os.path.join(DATA_DIR, "缺磷数据预处理_test_set"), transform=transform),
    label_offset=1,
)

val_loader = DataLoader(ConcatDataset([val_health, val_def]), batch_size=32, shuffle=False)
test_loader = DataLoader(ConcatDataset([test_health, test_def]), batch_size=32, shuffle=False)

model = resnet18(weights=None)
model.fc = nn.Linear(model.fc.in_features, 2)
model.load_state_dict(torch.load(MODEL_PATH, map_location="cpu"))
model.eval()


def evaluate(loader):
    correct, total = 0, 0
    with torch.no_grad():
        for inputs, labels in loader:
            out = model(inputs)
            _, pred = out.max(1)
            correct += (pred == labels).sum().item()
            total += labels.size(0)
    return 100 * correct / total


print(f"ResNet18 模型评估:")
print(f"Validation Accuracy: {evaluate(val_loader):.2f}%")
print(f"Test Accuracy: {evaluate(test_loader):.2f}%")
