"""
烟草缺钾分类 - ResNet18 迁移学习训练脚本
相比 AlexNet 提升准确度：预训练 backbone + 数据增强 + 正确标签
"""
import torch
import torch.nn as nn
import torch.optim as optim
from torch.optim.lr_scheduler import StepLR
from torchvision import datasets, transforms
from torchvision.models import resnet18, ResNet18_Weights
from torch.utils.data import DataLoader, ConcatDataset
import os

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(os.path.dirname(SCRIPT_DIR), "模型部署数据集")
# 权重直接保存到后端 drf_test002/model_weights，供 Django 缺素推理加载
MODEL_DIR = os.path.normpath(os.path.join(SCRIPT_DIR, "..", "前后端", "drf_test002", "model_weights"))
os.makedirs(MODEL_DIR, exist_ok=True)

# 健康=0, 缺钾=1（原“缺磷”目录中的图片文件名均为 potassium_deficiency）
class RemapLabelDataset(torch.utils.data.Dataset):
    def __init__(self, dataset, label_offset=0):
        self.dataset = dataset
        self.offset = label_offset

    def __len__(self):
        return len(self.dataset)

    def __getitem__(self, idx):
        img, lbl = self.dataset[idx]
        return img, lbl + self.offset


def get_dataloaders():
    # 训练数据增强
    train_transform = transforms.Compose([
        transforms.Resize((256, 256)),
        transforms.RandomCrop(224),
        transforms.RandomHorizontalFlip(),
        transforms.RandomVerticalFlip(),
        transforms.ColorJitter(brightness=0.2, contrast=0.2, saturation=0.2),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    # 验证/测试：无增强
    eval_transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

    train_health = datasets.ImageFolder(
        os.path.join(DATA_DIR, "healthy_validation_set"), transform=train_transform
    )
    train_deficiency = RemapLabelDataset(
        datasets.ImageFolder(
            os.path.join(DATA_DIR, "缺磷数据预处理_validation_set"), transform=train_transform
        ),
        label_offset=1,
    )
    train_dataset = ConcatDataset([train_health, train_deficiency])

    test_health = datasets.ImageFolder(
        os.path.join(DATA_DIR, "healthy_test_set"), transform=eval_transform
    )
    test_deficiency = RemapLabelDataset(
        datasets.ImageFolder(
            os.path.join(DATA_DIR, "缺磷数据预处理_test_set"), transform=eval_transform
        ),
        label_offset=1,
    )
    test_dataset = ConcatDataset([test_health, test_deficiency])

    train_loader = DataLoader(train_dataset, batch_size=32, shuffle=True, num_workers=0, pin_memory=True)
    test_loader = DataLoader(test_dataset, batch_size=32, shuffle=False, num_workers=0)
    return train_loader, test_loader


def build_model(num_classes=2):
    """ResNet18 预训练 + 替换最后一层"""
    weights = ResNet18_Weights.IMAGENET1K_V1
    model = resnet18(weights=weights)
    in_features = model.fc.in_features
    model.fc = nn.Linear(in_features, num_classes)
    return model


def train_epoch(model, loader, criterion, optimizer, device):
    model.train()
    total_loss, correct, total = 0.0, 0, 0
    for inputs, labels in loader:
        inputs, labels = inputs.to(device), labels.to(device)
        optimizer.zero_grad()
        outputs = model(inputs)
        loss = criterion(outputs, labels)
        loss.backward()
        optimizer.step()
        total_loss += loss.item()
        _, pred = outputs.max(1)
        correct += (pred == labels).sum().item()
        total += labels.size(0)
    return total_loss / len(loader), 100 * correct / total


def evaluate(model, loader, device):
    model.eval()
    correct, total = 0, 0
    with torch.no_grad():
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, pred = outputs.max(1)
            correct += (pred == labels).sum().item()
            total += labels.size(0)
    return 100 * correct / total if total > 0 else 0.0


def main():
    device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    print(f"Device: {device}")

    train_loader, test_loader = get_dataloaders()
    model = build_model(num_classes=2)
    model = model.to(device)

    criterion = nn.CrossEntropyLoss()
    optimizer = optim.Adam(model.parameters(), lr=1e-3)
    scheduler = StepLR(optimizer, step_size=5, gamma=0.5)

    best_acc = 0.0
    epochs = 20

    for ep in range(epochs):
        loss, train_acc = train_epoch(model, train_loader, criterion, optimizer, device)
        test_acc = evaluate(model, test_loader, device)
        scheduler.step()

        if test_acc > best_acc:
            best_acc = test_acc
            path = os.path.join(MODEL_DIR, "model_resnet18.pth")
            torch.save(model.state_dict(), path)
            print(f"Epoch {ep+1}/{epochs} | Loss: {loss:.4f} | Train: {train_acc:.1f}% | Test: {test_acc:.1f}% [saved]")
        else:
            print(f"Epoch {ep+1}/{epochs} | Loss: {loss:.4f} | Train: {train_acc:.1f}% | Test: {test_acc:.1f}%")

    print(f"\nBest Test Accuracy: {best_acc:.2f}%")
    print(f"Model saved to: {os.path.join(MODEL_DIR, 'model_resnet18.pth')}")


if __name__ == "__main__":
    main()
