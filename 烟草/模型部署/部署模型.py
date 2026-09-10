import torch
import torch.nn as nn
import torch.optim as optim
from torchvision import datasets, transforms
from torch.utils.data import DataLoader
import torch.jit
# 定义AlexNet模型
class AlexNet(nn.Module):
    def __init__(self, num_classes=1000):
        super(AlexNet, self).__init__()
        self.features = nn.Sequential(
            nn.Conv2d(3, 64, kernel_size=11, stride=4, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
            nn.Conv2d(64, 192, kernel_size=5, padding=2),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
            nn.Conv2d(192, 384, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(384, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.Conv2d(256, 256, kernel_size=3, padding=1),
            nn.ReLU(inplace=True),
            nn.MaxPool2d(kernel_size=3, stride=2),
        )
        self.avgpool = nn.AdaptiveAvgPool2d((6, 6))
        self.classifier = nn.Sequential(
            nn.Dropout(),
            nn.Linear(256 * 6 * 6, 4096),
            nn.ReLU(inplace=True),
            nn.Dropout(),
            nn.Linear(4096, 4096),
            nn.ReLU(inplace=True),
            nn.Linear(4096, num_classes),
        )

    def forward(self, x):
        x = self.features(x)
        x = self.avgpool(x)
        x = torch.flatten(x, 1)
        x = self.classifier(x)
        return x
model = AlexNet(num_classes=2)  # 创建模型实例
transform = transforms.Compose([
    transforms.Resize((227, 227)),  # 如果需要调整图片大小
    transforms.ToTensor(),  # 将图片转换为Tensor
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),  # 归一化
])

# 加载图像数据集

val_dataset_health = datasets.ImageFolder(root=r"E:\烟草\模型部署数据集\healthy_validation_set", transform=transform)
test_dataset_health = datasets.ImageFolder(root=r"E:\烟草\模型部署数据集\healthy_test_set", transform=transform)


val_dataset_deficiency = datasets.ImageFolder(root=r"E:\烟草\模型部署数据集\缺磷数据预处理_validation_set", transform=transform)
test_dataset_deficiency = datasets.ImageFolder(root=r"E:\烟草\模型部署数据集\缺磷数据预处理_test_set", transform=transform)

# 将相同分割的数据集合并

val_dataset = torch.utils.data.ConcatDataset([val_dataset_health, val_dataset_deficiency])
test_dataset = torch.utils.data.ConcatDataset([test_dataset_health, test_dataset_deficiency])

# 创建数据加载器
batch_size = 32
val_loader = DataLoader(val_dataset, batch_size=batch_size, shuffle=False)
test_loader = DataLoader(test_dataset, batch_size=batch_size, shuffle=False)
device = torch.device("cuda" if torch.cuda.is_available() else "cpu")  # 检测是否有GPU
model.to(device)  # 将模型移动到GPU（如果有的话）
def evaluate_model(loader):
    model.eval()  # 设置模型为评估模式
    correct = 0
    total = 0
    with torch.no_grad():  # 在评估模式下，不计算梯度
        for inputs, labels in loader:
            inputs, labels = inputs.to(device), labels.to(device)
            outputs = model(inputs)
            _, predicted = torch.max(outputs.data, 1)
            total += labels.size(0)
            correct += (predicted == labels).sum().item()
    accuracy = 100 * correct / total
    return accuracy

# 加载模型权重
PATH = r"E:\烟草\模型部署\models\model_weights.pth"  # 指定保存路径

model.load_state_dict(torch.load(PATH))
model.eval()  # 设置模型为评估模式
val_accuracy = evaluate_model(val_loader)
print(f'Validation Accuracy: {val_accuracy}%')

model.eval()  # 设置模型为评估模式
test_accuracy = evaluate_model(test_loader)
print(f'Test Accuracy: {test_accuracy}%')

