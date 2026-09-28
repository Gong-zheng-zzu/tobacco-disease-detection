#!/usr/bin/env python
# -*- coding: utf-8 -*-
import os
import sys
sys.path.insert(0, r'D:\烟草\烟草\前后端\drf_test002')
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'drf_test002.settings')

import django
django.setup()

# 重新加载模块
import importlib
from app2.views import unified_detection
importlib.reload(unified_detection)

from app2.views.unified_detection import _run_unified_detection
from PIL import Image

test_img = r'D:\烟草\烟草\unified_tobacco_dataset\images\test\deficiency_k_1.jpg'
print(f'测试图像: {test_img}')

img = Image.open(test_img).convert('RGB')
result, err = _run_unified_detection(img, conf_threshold=0.25)

if err:
    print(f'错误: {err}')
else:
    print('\n检测结果:')
    diseases = result.get('diseases')
    is_healthy = result.get('is_healthy')
    is_deficiency_k = result.get('is_deficiency_k')
    all_detected = result.get('all_detected')
    confidence = result.get('confidence')

    print(f'  病害: {diseases}')
    print(f'  健康: {is_healthy}')
    print(f'  缺钾: {is_deficiency_k}')
    print(f'  所有检测: {all_detected}')
    print(f'  置信度: {confidence}')
