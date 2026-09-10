import cv2
import torch.nn as nn
import torch
from PIL import Image
import os
import numpy as np
from torchvision import transforms

# 定义模型
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

# 定义模型
model = AlexNet(num_classes=2)

# 加载模型权重（使用脚本所在目录，避免路径问题）
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
PATH = os.path.join(SCRIPT_DIR, "models", "model_weights.pth")
if not os.path.exists(PATH):
    raise FileNotFoundError(f"模型文件不存在: {PATH}")
model.load_state_dict(torch.load(PATH, map_location=torch.device('cpu')))

# 定义数据转换
transform = transforms.Compose([
    transforms.Resize((227, 227)),  # 确保输入图像大小为227x227
    transforms.ToTensor(),
    transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
])

# 从本地文件获取图像
def get_image_from_file(file_path):
    image = Image.open(file_path).convert("RGB")
    return np.array(image)

# 使用模型进行预测
def predict_image(model, image):
    image = Image.fromarray(image)
    image = transform(image)
    image = torch.unsqueeze(image, 0)  # 增加一个批次维度

    # 预测
    with torch.no_grad():
        prediction = model(image)
        predicted_class = prediction[0].argmax().item()  # 获取预测的类别

    return predicted_class

# 主函数
def main():
    # 测试图片目录：优先 E:\烟草\目标检测图片\测试用，否则用项目下 目标检测图片\测试用
    folder_path = r"E:\烟草\目标检测图片\测试用"
    if not os.path.exists(folder_path):
        folder_path = os.path.join(os.path.dirname(SCRIPT_DIR), "目标检测图片", "测试用")
    if not os.path.exists(folder_path):
        print(f"目录 {folder_path} 不存在")
        return

    # 结果统一保存到「模型部署/results」文件夹（英文路径避免 cv2 保存失败）
    output_dir = os.path.join(SCRIPT_DIR, "results")
    os.makedirs(output_dir, exist_ok=True)

    count = 0
    saved_paths = []
    for file_name in os.listdir(folder_path):
        if file_name.lower().endswith(('.jpg', '.jpeg', '.png')):
            file_path = os.path.join(folder_path, file_name)
            image = get_image_from_file(file_path)
            if image is not None:
                predicted_class = predict_image(model, image)
                print(f"文件 {file_name} 的预测结果: {predicted_class}")

                # 结果文件名：原文件名_class类别.jpg
                base_name = os.path.splitext(file_name)[0]
                result_name = f"{base_name}_class{predicted_class}.jpg"
                result_image_path = os.path.join(output_dir, result_name)
                # 用 imencode + 文件写入，避免 cv2.imwrite 在中文路径下保存失败
                bgr = cv2.cvtColor(image, cv2.COLOR_RGB2BGR)
                ok, buf = cv2.imencode(".jpg", bgr)
                if ok:
                    with open(result_image_path, "wb") as f:
                        f.write(buf.tobytes())
                if ok:
                    result_image_path = os.path.abspath(result_image_path)
                    saved_paths.append(result_image_path)
                    print(f"已保存: {result_image_path}")
                else:
                    print(f"保存失败: {result_image_path}")
                count += 1

    if saved_paths:
        print(f"\n共处理 {count} 张图，结果在: {os.path.abspath(output_dir)}")
        try:
            os.startfile(os.path.abspath(output_dir))  # 运行结束后自动打开结果文件夹
        except Exception:
            pass

if __name__ == "__main__":
    main()
