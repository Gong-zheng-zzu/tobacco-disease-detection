"""
统一病害&营养检测API - 使用YOLOv8 6类模型
支持一次检测识别：4种病害 + 健康 + 缺钾
"""
import io
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from ..models import User, LandParcel, NutrientDeficiency, Fer_region_record
from ..serializer import FerRegionCreateSerializer, FerRegionSerializer

# 统一6类检测：4病害 + 健康 + 缺钾
CLASS_NAMES = {
    0: 'baixingbing',    # 白星病
    1: 'huayebing',      # 花叶病
    2: 'yanqingchong',   # 烟青虫
    3: 'yehuobing',      # 野火病
    4: 'healthy',        # 健康
    5: 'deficiency_k'    # 缺钾
}

CLASS_TO_CN = {
    'baixingbing': '白星病',
    'huayebing': '花叶病',
    'yanqingchong': '烟青虫',
    'yehuobing': '野火病',
    'healthy': '健康',
    'deficiency_k': '缺钾'
}

# 类别自适应置信度阈值（后处理优化 - 修正版）
CLASS_CONF_THRESHOLDS = {
    '白星病': 0.36,      # 轻微提高，减少误报同时保持召回率
    '花叶病': 0.36,      # 轻微提高，减少误报同时保持召回率
    '烟青虫': 0.25,      # 降低阈值，提高小目标召回率
    '野火病': 0.35,      # 标准阈值
    '健康': 0.35,        # 标准阈值
    '缺钾': 0.35,        # 标准阈值
}

# 延迟加载统一YOLO模型
_UNIFIED_MODEL = None
_BASE_DRF = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
_DEFAULT_WEIGHTS_DIR = os.path.join(_BASE_DRF, "model_weights")
DEFAULT_UNIFIED_MODEL_PATH = os.path.normpath(os.path.join(_DEFAULT_WEIGHTS_DIR, "yolo_unified_6class_best.pt"))


def apply_post_processing(detected_classes, confidences):
    """
    应用后处理规则（最小化版本）：
    仅处理健康+病害逻辑矛盾，保留所有其他多标签检测

    Args:
        detected_classes: set of English class names
        confidences: dict mapping English class names to confidence scores

    Returns:
        (filtered_detected_classes, filtered_confidences)
    """
    filtered = confidences.copy()
    detected = detected_classes.copy()

    # 步骤2：健康+病害逻辑检查
    if 'healthy' in detected and len(detected) > 1:
        # 如果有其他病害且置信度更高，移除健康
        other_confs = [filtered[d] for d in detected if d != 'healthy']
        if other_confs and max(other_confs) > filtered['healthy']:
            detected.remove('healthy')
            del filtered['healthy']

    return detected, filtered


def _get_unified_model():
    """获取统一检测模型（延迟加载）"""
    global _UNIFIED_MODEL
    if _UNIFIED_MODEL is not None:
        return _UNIFIED_MODEL
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise RuntimeError("统一检测需要安装 ultralytics，请执行: pip install ultralytics") from e

    model_path = getattr(settings, "UNIFIED_MODEL_PATH", None) or DEFAULT_UNIFIED_MODEL_PATH
    if not os.path.exists(model_path):
        import logging
        logging.getLogger(__name__).warning("统一模型文件不存在: %s", model_path)
        return None

    try:
        _UNIFIED_MODEL = YOLO(model_path)
        print(f"[统一检测] 模型已加载: {model_path}")
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("统一模型加载失败: %s", e)
        return None

    return _UNIFIED_MODEL


def _run_unified_detection(image_source, conf_threshold=0.35):
    """
    执行统一检测（病害+健康+缺钾）
    返回: (result_dict, error_msg)
    result_dict = {
        'diseases': ['白星病', '烟青虫'],  # 检测到的病害
        'is_healthy': False,                # 是否健康
        'is_deficiency_k': True,            # 是否缺钾
        'all_detected': ['白星病', '烟青虫', '缺钾'],  # 所有检测结果
        'confidence': {...}                  # 各类别置信度
    }
    """
    try:
        model = _get_unified_model()
        if model is None:
            return None, "统一模型未加载，请确认模型路径: " + DEFAULT_UNIFIED_MODEL_PATH

        try:
            from PIL import Image
        except ImportError:
            return None, "需要 Pillow"

        # 处理图像输入 - 直接传PIL Image或文件路径，不转numpy
        if isinstance(image_source, str):
            img = image_source  # 文件路径
        elif hasattr(image_source, "convert"):
            img = image_source  # PIL Image对象
        else:
            img = image_source

        # 运行推理 - 优化后处理参数
        # conf=0.35: 提高置信度阈值，减少误报
        # iou=0.4: 降低IoU阈值，允许重叠检测（适合小目标聚集）
        # agnostic_nms=True: 跨类别NMS，减少白星病-花叶病重复检测
        results = model.predict(
            source=img,
            conf=conf_threshold,
            iou=0.4,
            agnostic_nms=True,
            verbose=False
        )

        detected_classes = set()
        confidences = {}

        for r in results:
            if r.boxes is not None and len(r.boxes) > 0:
                for box_idx in range(len(r.boxes)):
                    cls_id = int(r.boxes.cls[box_idx])
                    conf = float(r.boxes.conf[box_idx])

                    if cls_id in CLASS_NAMES:
                        class_name = CLASS_NAMES[cls_id]
                        detected_classes.add(class_name)
                        # 保存最高置信度
                        if class_name not in confidences or conf > confidences[class_name]:
                            confidences[class_name] = conf

        # 应用后处理优化
        detected_classes, confidences = apply_post_processing(detected_classes, confidences)

        # 分类结果
        diseases = []
        is_healthy = 'healthy' in detected_classes
        is_deficiency_k = 'deficiency_k' in detected_classes

        for cls in detected_classes:
            if cls in ['baixingbing', 'huayebing', 'yanqingchong', 'yehuobing']:
                diseases.append(CLASS_TO_CN[cls])

        all_detected = [CLASS_TO_CN[cls] for cls in detected_classes]

        result = {
            'diseases': diseases,
            'is_healthy': is_healthy,
            'is_deficiency_k': is_deficiency_k,
            'all_detected': all_detected,
            'confidence': {CLASS_TO_CN[k]: v for k, v in confidences.items()}
        }

        return result, None

    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("统一检测异常: %s", e)
        return None, str(e)


class UnifiedDetectionView(APIView):
    """统一检测API：一次检测识别病害、健康、缺钾"""
    authentication_classes = []
    permission_classes = []

    def post(self, request, user_id, fieldnum):
        if "image" not in request.FILES:
            return Response({"error": "请上传图片", "code": 400}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(pk=user_id)
            field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
            if not field:
                return Response({"error": "不存在该地块", "code": 400}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"error": "不存在该用户", "code": 400}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from PIL import Image
            image = Image.open(io.BytesIO(request.FILES["image"].read())).convert("RGB")
        except Exception as e:
            return Response({"error": f"图像加载失败: {str(e)}", "code": 400}, status=status.HTTP_400_BAD_REQUEST)

        # 运行统一检测
        result, err = _run_unified_detection(image)

        if err:
            return Response({"error": err, "code": 503}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if result is None:
            return Response({"error": "检测失败", "code": 503}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        # 构造响应
        response_data = {
            "code": 200,
            "result": result,
            "message": ""
        }

        # 如果检测到缺钾，记录并生成追肥建议
        if result['is_deficiency_k']:
            deficiency = NutrientDeficiency.objects.create(
                parcel=field,
                nutrient_type='K',  # 缺钾
                intensity=0.5
            )

            # 生成追肥建议
            fer_region, fer_err = self._create_fer_region_for_deficiency(field, 'K', 0.5)
            if fer_region:
                fer_region.deficiencies.add(deficiency)
                response_data["fer_region"] = FerRegionSerializer(fer_region).data
                response_data["message"] = "已检测到缺钾，已记录并生成追肥建议"
            else:
                response_data["message"] = "已记录缺钾，追肥记录创建失败"

        # 如果检测到病害，添加提示
        if result['diseases']:
            disease_msg = "检测到病害: " + "、".join(result['diseases'])
            response_data["message"] = response_data.get("message", "") + (" | " if response_data.get("message") else "") + disease_msg

        # 如果健康
        if result['is_healthy'] and not result['diseases'] and not result['is_deficiency_k']:
            response_data["message"] = "烟草叶片健康"

        return Response(response_data, status=status.HTTP_200_OK)

    def _create_fer_region_for_deficiency(self, field, nutrient_type, intensity=0.5):
        """为单条缺素记录创建追肥记录"""
        field_area_m2 = float(field.area)
        total_area_m2 = field_area_m2 * 0.3
        factor = 0.5 + float(intensity) * 0.5
        base_unit = 2000 / 3
        base_volume = (field_area_m2 / base_unit) * 75
        area_ratio = total_area_m2 / field_area_m2
        extra_volume = base_volume * area_ratio * 0.3 * factor

        extra_n = extra_volume if nutrient_type == 'N' else 0
        extra_p = extra_volume if nutrient_type == 'P' else 0
        extra_k = extra_volume if nutrient_type == 'K' else 0

        fer_region_data = {"parcel": field.id}
        serializer = FerRegionCreateSerializer(data=fer_region_data)
        if not serializer.is_valid():
            return None, serializer.errors
        fer_region = serializer.save()
        fer_region.extra_n_used = extra_n
        fer_region.extra_p_used = extra_p
        fer_region.extra_k_used = extra_k
        fer_region.save()
        return fer_region, None


class SimpleUnifiedDetectionView(APIView):
    """简单统一检测：只返回检测结果，不关联地块"""
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        if "image" not in request.FILES:
            return Response({"error": "请上传图片", "code": 400}, status=status.HTTP_400_BAD_REQUEST)

        try:
            from PIL import Image
            image = Image.open(io.BytesIO(request.FILES["image"].read())).convert("RGB")
        except Exception as e:
            return Response({"error": f"图像加载失败: {str(e)}", "code": 400}, status=status.HTTP_400_BAD_REQUEST)

        result, err = _run_unified_detection(image)

        if err:
            return Response({"error": err, "code": 503}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        if result is None:
            return Response({"error": "检测失败", "code": 503}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        return Response({"code": 200, "result": result}, status=status.HTTP_200_OK)
