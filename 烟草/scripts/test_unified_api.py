#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
测试统一检测API端点
确保Django后端集成正常工作
"""
import requests
from pathlib import Path

# API配置
BASE_URL = "http://127.0.0.1:8000"
SIMPLE_DETECT_URL = f"{BASE_URL}/api/unified_detect/"

# 测试图像路径
TEST_IMAGE_DIR = Path(r"D:\烟草\烟草\unified_tobacco_dataset\images\test")


def test_simple_detection():
    """测试简单检测端点（不关联地块）"""
    print("=" * 60)
    print("测试统一检测API - 简单模式")
    print("=" * 60)

    # 测试每个类别的样本
    test_cases = {
        'deficiency_k': 'deficiency_k_',  # 缺钾样本前缀
        'baixingbing': 'baixingbing_',     # 白星病样本前缀
        'healthy': 'healthy_',             # 健康样本前缀
        'huayebing': 'huayebing_',         # 花叶病样本前缀
        'yanqingchong': 'yanqingchong_',   # 烟青虫样本前缀
    }

    for class_name, prefix in test_cases.items():
        # 找到该类别的测试图像
        sample_images = list(TEST_IMAGE_DIR.glob(f"{prefix}*.jpg"))
        sample_images.extend(TEST_IMAGE_DIR.glob(f"{prefix}*.JPG"))  # 包含大写扩展名

        if not sample_images:
            print(f"\n⚠️  未找到 {class_name} 样本 (前缀: {prefix})")
            continue

        test_image = sample_images[0]
        print(f"\n测试 {class_name}: {test_image.name}")

        try:
            with open(test_image, 'rb') as f:
                files = {'image': f}
                response = requests.post(SIMPLE_DETECT_URL, files=files, timeout=30)

            if response.status_code == 200:
                result = response.json()
                print(f"✅ 响应成功")
                print(f"   检测结果: {result.get('result', {}).get('all_detected', [])}")
                print(f"   是否健康: {result.get('result', {}).get('is_healthy', False)}")
                print(f"   是否缺钾: {result.get('result', {}).get('is_deficiency_k', False)}")
                print(f"   病害: {result.get('result', {}).get('diseases', [])}")

                # 验证结果正确性
                detection = result.get('result', {})
                if class_name == 'deficiency_k' and detection.get('is_deficiency_k'):
                    print(f"   ✓ 缺钾识别正确")
                elif class_name == 'healthy' and detection.get('is_healthy'):
                    print(f"   ✓ 健康识别正确")
                elif class_name == 'baixingbing' and '白星病' in detection.get('diseases', []):
                    print(f"   ✓ 白星病识别正确")
                elif class_name == 'huayebing' and '花叶病' in detection.get('diseases', []):
                    print(f"   ✓ 花叶病识别正确")
                elif class_name == 'yanqingchong' and '烟青虫' in detection.get('diseases', []):
                    print(f"   ✓ 烟青虫识别正确")
                else:
                    print(f"   ⚠️  识别结果与预期不符")
                    if class_name == 'deficiency_k' and not detection.get('is_deficiency_k'):
                        print(f"   ❌ 缺钾样本未被识别为缺钾！")
                    if class_name == 'deficiency_k' and '白星病' in detection.get('diseases', []):
                        print(f"   ❌ 缺钾样本被误判为白星病！")

            else:
                print(f"❌ 请求失败: {response.status_code}")
                print(f"   响应: {response.text}")

        except requests.exceptions.ConnectionError:
            print(f"❌ 无法连接到服务器: {BASE_URL}")
            print(f"   请确保Django服务已启动: python manage.py runserver")
            return
        except Exception as e:
            print(f"❌ 测试失败: {e}")

    print("\n" + "=" * 60)
    print("测试完成")
    print("=" * 60)


def test_field_detection():
    """测试关联地块的检测端点"""
    print("\n" + "=" * 60)
    print("测试统一检测API - 地块模式")
    print("=" * 60)

    # 需要真实的用户ID和地块ID
    user_id = 1
    field_id = 1
    field_detect_url = f"{BASE_URL}/api/user/{user_id}/field/{field_id}/unified_detect/"

    # 测试缺钾样本（会自动创建追肥记录）
    deficiency_samples = list(TEST_IMAGE_DIR.glob("deficiency_k_*.jpg"))
    deficiency_samples.extend(TEST_IMAGE_DIR.glob("deficiency_k_*.JPG"))

    if not deficiency_samples:
        print("⚠️  未找到缺钾样本")
        return

    test_image = deficiency_samples[0]
    print(f"\n测试缺钾识别（关联地块）: {test_image.name}")

    try:
        with open(test_image, 'rb') as f:
            files = {'image': f}
            response = requests.post(field_detect_url, files=files, timeout=30)

        if response.status_code == 200:
            result = response.json()
            print(f"✅ 响应成功")
            print(f"   检测结果: {result.get('result', {}).get('all_detected', [])}")
            print(f"   消息: {result.get('message', '')}")

            if 'fer_region' in result:
                print(f"   ✓ 已自动生成追肥记录")
                fer = result['fer_region']
                print(f"     追肥钾量: {fer.get('extra_k_used', 0)} kg")
        else:
            print(f"❌ 请求失败: {response.status_code}")
            print(f"   响应: {response.text}")

    except requests.exceptions.ConnectionError:
        print(f"❌ 无法连接到服务器: {BASE_URL}")
        print(f"   请确保Django服务已启动")
    except Exception as e:
        print(f"❌ 测试失败: {e}")

    print("\n" + "=" * 60)


if __name__ == '__main__':
    print("\n🚀 开始测试统一检测API\n")
    test_simple_detection()

    # 可选：测试地块模式（需要数据库中有用户和地块）
    # test_field_detection()
