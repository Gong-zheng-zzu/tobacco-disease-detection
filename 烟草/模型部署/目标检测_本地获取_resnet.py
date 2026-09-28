"""
烟草缺钾分类 - ResNet18 高精度版本
基于 目标检测_本地获取.py 重写，使用 ResNet18 替代 AlexNet 提升准确度
"""
import cv2
import torch
import torch.nn as nn
from torchvision import transforms
from torchvision.models import resnet18
from PIL import Image
import os
import numpy as np

# 类别名（0=健康, 1=缺钾；原目录名缺磷是历史命名错误）
CLASS_NAMES = ["健康", "缺钾"]


def build_model(num_classes=2, weights_path=None, device=None):
    """构建 ResNet18 二分类模型，支持 GPU 加速"""
    if device is None:
        device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    map_loc = "cuda" if device.type == "cuda" else "cpu"
    model = resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    if weights_path and os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location=map_loc))
    return model.to(device)


# 脚本目录
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_PATH = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "前后端", "drf_test002", "model_weights", "model_resnet18.pth")
)
if not os.path.isfile(MODEL_PATH):
    MODEL_PATH = os.path.join(SCRIPT_DIR, "models", "model_resnet18.pth")

# 若 ResNet18 权重不存在，回退到旧 AlexNet
USE_RESNET = os.path.exists(MODEL_PATH)
DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")

if USE_RESNET:
    model = build_model(num_classes=2, weights_path=MODEL_PATH, device=DEVICE)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
else:
    # 回退到 AlexNet
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

    model = AlexNet(num_classes=2)
    old_path = os.path.join(SCRIPT_DIR, "models", "model_weights.pth")
    map_loc = "cuda" if DEVICE.type == "cuda" else "cpu"
    if os.path.exists(old_path):
        model.load_state_dict(torch.load(old_path, map_location=map_loc))
    model = model.to(DEVICE)
    transform = transforms.Compose([
        transforms.Resize((227, 227)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])

model.eval()


def get_image_from_file(file_path):
    image = Image.open(file_path).convert("RGB")
    return np.array(image)


def predict_image(model, image):
    img_pil = Image.fromarray(image)
    img_t = transform(img_pil).unsqueeze(0).to(DEVICE)
    infer_mode = getattr(torch, "inference_mode", torch.no_grad)
    with infer_mode():
        prediction = model(img_t)
        predicted_class = prediction[0].argmax().item()
    return predicted_class


def main():
    folder_path = os.path.join(os.path.dirname(SCRIPT_DIR), "目标检测图片", "测试用")
    if not os.path.exists(folder_path):
        folder_path = os.path.join(SCRIPT_DIR, "..", "目标检测图片", "测试用")
    if not os.path.exists(folder_path):
        folder_path = r"E:\烟草\目标检测图片\测试用"
    if not os.path.exists(folder_path):
        print(f"目录不存在: {folder_path}")
        return

    output_dir = os.path.join(SCRIPT_DIR, "results")
    os.makedirs(output_dir, exist_ok=True)

    model_name = "ResNet18" if USE_RESNET else "AlexNet"
    dev_name = "CUDA" if DEVICE.type == "cuda" else "CPU"
    print(f"使用模型: {model_name} | 推理设备: {dev_name}\n")

    count = 0
    saved_paths = []
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith((".jpg", ".jpeg", ".png")):
            file_path = os.path.join(folder_path, file_name)
            image = get_image_from_file(file_path)
            if image is not None:
                predicted_class = predict_image(model, image)
                class_name = CLASS_NAMES[predicted_class]
                print(f"{file_name} -> {class_name} (class {predicted_class})")

                base_name = os.path.splitext(file_name)[0]
                result_name = f"{base_name}_class{predicted_class}_{class_name}.jpg"
                result_image_path = os.path.join(output_dir, result_name)
                bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                ok, buf = cv2.imencode(".jpg", bgr)
                if ok:
                    with open(result_image_path, "wb") as f:
                        f.write(buf.tobytes())
                    saved_paths.append(os.path.abspath(result_image_path))
                    print(f"  已保存: {result_image_path}")
                count += 1

    if saved_paths:
        print(f"\n共处理 {count} 张图，结果在: {os.path.abspath(output_dir)}")
        try:
            os.startfile(os.path.abspath(output_dir))
        except Exception:
            pass


if __name__ == "__main__":
    main()
