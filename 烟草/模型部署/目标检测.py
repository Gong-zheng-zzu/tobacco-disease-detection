import cv2
import torch.nn as nn
import torch
from PIL import Image
import os
import numpy as np
from torchvision import transforms
from torchvision.models import resnet18


def build_model(num_classes=2, weights_path=None):
    """构建 ResNet18 二分类模型"""
    model = resnet18(weights=None)
    model.fc = nn.Linear(model.fc.in_features, num_classes)
    if weights_path and os.path.exists(weights_path):
        model.load_state_dict(torch.load(weights_path, map_location="cpu"))
    return model


# 类别：0=健康, 1=缺磷
CLASS_NAMES = ["健康", "缺磷"]

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_RESNET = os.path.normpath(
    os.path.join(SCRIPT_DIR, "..", "前后端", "drf_test002", "model_weights", "model_resnet18.pth")
)
if not os.path.isfile(MODEL_RESNET):
    MODEL_RESNET = os.path.join(SCRIPT_DIR, "models", "model_resnet18.pth")
MODEL_ALEX = os.path.join(SCRIPT_DIR, "models", "model_weights.pth")
USE_RESNET = os.path.exists(MODEL_RESNET)

if USE_RESNET:
    model = build_model(num_classes=2, weights_path=MODEL_RESNET)
    transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    print("已加载 ResNet18 模型")
else:
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
    if os.path.exists(MODEL_ALEX):
        model.load_state_dict(torch.load(MODEL_ALEX, map_location="cpu"))
    transform = transforms.Compose([
        transforms.Resize((227, 227)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    print("已加载 AlexNet 模型（未找到 model_resnet18.pth）")

model.eval()

# 从摄像头获取图像
def get_image_from_camera(cap):
    ret, frame = cap.read()
    if not ret:
        print("无法从摄像头读取图像")
        return None
    return cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)


def save_image_cn_path(folder_path, filename, image_bgr):
    """保存图片到含中文的路径：用 imencode + 文件写入，避免 cv2.imwrite 失败"""
    out_path = os.path.join(folder_path, filename)
    ok, buf = cv2.imencode(".jpg", image_bgr)
    if ok:
        with open(out_path, "wb") as f:
            f.write(buf.tobytes())
    return ok


def predict_image(model, image):

    # 加载图像
    image = Image.fromarray(image)
    image = transform(image)
    image = torch.unsqueeze(image, 0)  # 增加一个批次维度

    # 预测
    with torch.no_grad():
        prediction = model(image)
        predicted_class = prediction[0].argmax().item()  # 获取预测的类别

    return predicted_class


def main():
    cap = cv2.VideoCapture(0)  # 打开摄像头
    if not cap.isOpened():
        print("无法打开摄像头")
        return

    folder_path = r"E:\烟草\目标检测图片\测试用"
    os.makedirs(folder_path, exist_ok=True)
    folder_abs = os.path.abspath(folder_path)
    print(f"抓拍图片将保存到: {folder_abs}")
    print("按回车拍照并识别，输入 q 回车退出\n")

    count = 0
    while True:
        line = input(">>> 按回车拍照（输入 q 退出）: ").strip().lower()
        if line == "q":
            print("已退出。")
            break
        image = get_image_from_camera(cap)
        if image is None:
            print("获取图像失败，请重试。")
            continue
        predicted_class = predict_image(model, image)
        print(f"预测结果: {CLASS_NAMES[predicted_class]}")
        bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
        if save_image_cn_path(folder_path, f"image_{predicted_class}_{count}.jpg", bgr):
            print(f"已保存: image_{predicted_class}_{count}.jpg\n")
        else:
            print("保存失败\n")
        count += 1

    cap.release()
    if count > 0:
        print(f"共保存 {count} 张，文件夹: {folder_abs}")
        try:
            os.startfile(folder_abs)
        except Exception:
            pass


if __name__ == "__main__":
    main()
