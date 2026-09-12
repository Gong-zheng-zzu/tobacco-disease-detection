import requests
from pathlib import Path

BASE_URL = 'http://127.0.0.1:8000'
TEST_DIR = Path(r'D:\烟草\烟草\unified_tobacco_dataset\images\test')

# 测试病害样本
test_cases = [
    ('白星病', 'Tobacco_Disease_100001.jpg'),
    ('缺钾', 'deficiency_k_1.jpg'),
    ('健康', 'healthy_0.jpg'),
]

print('=' * 60)
print('测试优化后的NMS参数效果')
print('=' * 60)

for label, filename in test_cases:
    img_path = TEST_DIR / filename
    if not img_path.exists():
        print(f'\n跳过 {label} - 文件不存在')
        continue

    print(f'\n测试 {label}: {filename}')
    with open(img_path, 'rb') as f:
        response = requests.post(
            f'{BASE_URL}/api/unified_detect/',
            files={'image': f},
            timeout=30
        )

    if response.status_code == 200:
        result = response.json()['result']
        all_detected = result.get('all_detected', [])
        confidence = result.get('confidence', {})
        print(f'  检测结果: {all_detected}')
        print(f'  置信度: {confidence}')
    else:
        print(f'  错误: {response.status_code}')
