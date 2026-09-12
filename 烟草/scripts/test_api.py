#!/usr/bin/env python
# -*- coding: utf-8 -*-
import requests
import json

# 测试图像
test_cases = [
    (r"D:\烟草\烟草\unified_tobacco_dataset\images\test\deficiency_k_1.jpg", "缺钾"),
    (r"D:\烟草\烟草\unified_tobacco_dataset\images\test\healthy_0.jpg", "健康"),
    (r"D:\烟草\烟草\unified_tobacco_dataset\images\test\Tobacco_Disease_100001.jpg", "白星病"),
    (r"D:\烟草\烟草\unified_tobacco_dataset\images\test\Tobacco_Disease_100325.jpg", "花叶病"),
    (r"D:\烟草\烟草\unified_tobacco_dataset\images\test\Tobacco_Disease_100409.jpg", "烟青虫"),
    (r"D:\烟草\烟草\unified_tobacco_dataset\images\test\Tobacco_Disease_100438.jpg", "野火病"),
]

url = "http://127.0.0.1:8000/api/unified_detect/"

for img_path, expected in test_cases:
    print(f"\n{'='*60}")
    print(f"测试: {expected} - {img_path}")
    print('='*60)

    with open(img_path, 'rb') as f:
        files = {'image': f}
        response = requests.post(url, files=files)

    if response.status_code == 200:
        result = response.json()
        print(f"✅ 状态: {response.status_code}")
        print(f"检测结果: {json.dumps(result, ensure_ascii=False, indent=2)}")
    else:
        print(f"❌ 错误: {response.status_code}")
        print(f"响应: {response.text}")
