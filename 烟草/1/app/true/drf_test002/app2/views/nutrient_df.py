import io
import os
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.conf import settings

from ..models import User, LandParcel, NutrientDeficiency, Fer_region_record
from ..serializer import FerRegionCreateSerializer, FerRegionSerializer

# ResNet18 二分类：0=健康, 1=缺钾（与 模型部署/train_resnet.py 一致）
CLASS_NAMES = ["健康", "缺钾"]

# 病虫害 YOLO 类别名（与 disease/data.yaml 一致）
DISEASE_NAME_MAP = {
    "baixingbing": "白星病",
    "huayebing": "黄叶病",
    "yanqingchong": "烟青虫",
    "yehuobing": "叶厚病",
}

# 延迟加载 torch 和模型
_MODEL = None
_transform = None
_DEVICE = None  # cuda/cpu，推理设备

# 病虫害 YOLO 模型（延迟加载）
_DISEASE_MODEL = None
# 默认权重目录：drf_test002/model_weights/（与 drf_test002/settings.py 中 MODEL_WEIGHTS_DIR 一致）
_BASE_DRF = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))  # .../drf_test002
_DEFAULT_WEIGHTS_DIR = os.path.join(_BASE_DRF, "model_weights")
DEFAULT_MODEL_PATH = os.path.normpath(os.path.join(_DEFAULT_WEIGHTS_DIR, "model_resnet18.pth"))
DEFAULT_DISEASE_MODEL_PATH = os.path.normpath(os.path.join(_DEFAULT_WEIGHTS_DIR, "yolov8n_best.pt"))


def _get_model_and_transform():
    """获取模型和 transform（首次调用时加载，支持 GPU 加速）"""
    global _MODEL, _transform, _DEVICE
    if _MODEL is not None and _transform is not None:
        return _MODEL, _transform
    try:
        import torch
        import torch.nn as nn
        from torchvision import transforms
        from torchvision.models import resnet18
    except ImportError as e:
        raise RuntimeError("缺素识别需要安装 torch、torchvision、Pillow，请执行: pip install torch torchvision Pillow") from e

    _DEVICE = torch.device("cuda" if torch.cuda.is_available() else "cpu")
    map_loc = "cuda" if torch.cuda.is_available() else "cpu"

    def build_model(num_classes=2, weights_path=None):
        model = resnet18(weights=None)
        model.fc = nn.Linear(model.fc.in_features, num_classes)
        if weights_path and os.path.exists(weights_path):
            state = torch.load(weights_path, map_location=map_loc)
            if isinstance(state, dict) and "model_state_dict" in state:
                model.load_state_dict(state["model_state_dict"])
            else:
                model.load_state_dict(state)
        return model.to(_DEVICE)

    model_path = getattr(settings, "NUTRIENT_DEFICIENCY_MODEL_PATH", None) or DEFAULT_MODEL_PATH
    if not os.path.exists(model_path):
        print(f"缺素识别模型文件不存在: {model_path}")
        return None, None

    _transform = transforms.Compose([
        transforms.Resize((224, 224)),
        transforms.ToTensor(),
        transforms.Normalize(mean=[0.485, 0.456, 0.406], std=[0.229, 0.224, 0.225]),
    ])
    _MODEL = build_model(num_classes=2, weights_path=model_path)
    _MODEL.eval()
    return _MODEL, _transform


def _preload_nutrient_model():
    """Django 启动时预加载模型，避免首次请求等待"""
    global _DEVICE
    try:
        _get_model_and_transform()
        dev = "CUDA" if (_DEVICE is not None and "cuda" in str(_DEVICE)) else "CPU"
        print(f"[缺素识别] 模型已预加载，推理设备: {dev}")
    except Exception as e:
        import logging
        logging.getLogger(__name__).warning("缺素模型预加载失败: %s", e)


def _get_disease_model():
    """获取病虫害 YOLO 模型（延迟加载）"""
    global _DISEASE_MODEL
    if _DISEASE_MODEL is not None:
        return _DISEASE_MODEL
    try:
        from ultralytics import YOLO
    except ImportError as e:
        raise RuntimeError("病虫害检测需要安装 ultralytics，请执行: pip install ultralytics") from e
    model_path = getattr(settings, "DISEASE_MODEL_PATH", None) or DEFAULT_DISEASE_MODEL_PATH
    if not os.path.exists(model_path):
        import logging
        logging.getLogger(__name__).warning("病虫害模型文件不存在: %s", model_path)
        return None
    try:
        _DISEASE_MODEL = YOLO(model_path)  # 赋值给全局（已声明 global）
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("病虫害模型加载失败: %s", e)
        return None
    return _DISEASE_MODEL


def _run_disease_recognition(image_source, conf_threshold=0.25):
    """
    执行病虫害 YOLO 检测。image_source 可为文件路径(str)、PIL.Image 或 numpy 数组。
    返回 (result_text, message)，如 ("检测到: 白星病、烟青虫", "") 或 ("未检测到病虫害", "")。
    """
    try:
        model = _get_disease_model()
        if model is None:
            return None, "病虫害模型未加载，请确认模型路径存在: " + (getattr(settings, "DISEASE_MODEL_PATH", None) or DEFAULT_DISEASE_MODEL_PATH)
        try:
            from PIL import Image
            import numpy as np
        except ImportError:
            return None, "需要 Pillow、numpy"
        if isinstance(image_source, str):
            img = np.array(Image.open(image_source).convert("RGB"))
        elif hasattr(image_source, "convert"):
            img = np.array(image_source.convert("RGB"))
        else:
            img = image_source
        results = model.predict(source=img, conf=conf_threshold, verbose=False)
        detected = set()
        names = getattr(model, "names", None) or {}
        # ultralytics 中 names 可能是 dict 或 list
        def get_class_name(cls_id):
            cid = int(cls_id)
            if isinstance(names, dict):
                return names.get(cid, str(cls_id))
            if isinstance(names, (list, tuple)) and 0 <= cid < len(names):
                return names[cid]
            return str(cls_id)
        for r in results:
            if r.boxes is not None:
                for cls_id in r.boxes.cls.cpu().int().tolist():
                    name = get_class_name(cls_id)
                    if isinstance(name, str):
                        detected.add(DISEASE_NAME_MAP.get(name, name))
        if not detected:
            return "未检测到病虫害", ""
        return "检测到: " + "、".join(sorted(detected)), ""
    except Exception as e:
        import logging
        logging.getLogger(__name__).exception("病虫害识别异常: %s", e)
        return None, str(e)


class ImageRecognitionView(APIView):
    authentication_classes = []
    permission_classes = []

    def post(self, request):
        if "image" not in request.FILES:
            return Response({"error": "No image provided"}, status=status.HTTP_400_BAD_REQUEST)

        image_file = request.FILES["image"]

        try:
            MODEL, transform = _get_model_and_transform()
        except RuntimeError as e:
            return Response({"error": str(e)}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if MODEL is None:
            return Response({
                "error": "缺素识别模型未加载，请确认模型文件存在"
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        try:
            from PIL import Image
            image = Image.open(io.BytesIO(image_file.read())).convert("RGB")
        except Exception as e:
            return Response({"error": f"图像加载失败: {str(e)}"}, status=status.HTTP_400_BAD_REQUEST)

        import torch
        img_t = transform(image).unsqueeze(0)
        if _DEVICE is not None and "cuda" in str(_DEVICE):
            img_t = img_t.to(_DEVICE)
        infer_mode = getattr(torch, "inference_mode", torch.no_grad)
        with infer_mode():
            logits = MODEL(img_t)
            predicted_class = logits[0].argmax().item()
        result_text = CLASS_NAMES[predicted_class] if 0 <= predicted_class < len(CLASS_NAMES) else "未知"
        return Response({"result": result_text}, status=status.HTTP_200_OK)


class NutrientRecognitionWithFieldView(APIView):
    """缺素识别（带地块选择）：识别结果会保存到缺素记录，若检测到缺素则自动生成追肥建议"""
    authentication_classes = []
    permission_classes = []

    def _run_recognition(self, image_source):
        """执行图像识别。image_source 可为文件路径(str)或 PIL.Image"""
        MODEL, transform = _get_model_and_transform()
        if MODEL is None:
            return None, "缺素识别模型未加载"
        import torch
        from PIL import Image
        if isinstance(image_source, str):
            image = Image.open(image_source).convert("RGB")
        else:
            image = image_source.convert("RGB") if hasattr(image_source, "convert") else image_source
        img_t = transform(image).unsqueeze(0)
        if _DEVICE is not None and "cuda" in str(_DEVICE):
            img_t = img_t.to(_DEVICE)
        infer_mode = getattr(torch, "inference_mode", torch.no_grad)
        with infer_mode():
            logits = MODEL(img_t)
            predicted_class = logits[0].argmax().item()
        return predicted_class, None

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

    def post(self, request, user_id, fieldnum):
        if "image" not in request.FILES:
            return Response({"error": "请上传图片", "code": 400}, status=status.HTTP_400_BAD_REQUEST)

        raw_mode = request.POST.get("mode") or request.data.get("mode") or request.query_params.get("mode") or "deficiency"
        mode = (raw_mode if isinstance(raw_mode, str) else str(raw_mode)).strip().lower()
        if mode not in ("deficiency", "disease"):
            mode = "deficiency"

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

        if mode == "disease":
            try:
                result_text, msg = _run_disease_recognition(image)
            except Exception as e:
                import logging
                logging.getLogger(__name__).exception("病虫害检测异常: %s", e)
                return Response({"error": f"病虫害检测异常: {e}", "code": 503}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            if result_text is None:
                return Response({"error": msg or "病虫害识别失败", "code": 503}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
            return Response({
                "result": result_text,
                "message": msg,
                "code": 200,
            }, status=status.HTTP_200_OK)

        try:
            MODEL, transform = _get_model_and_transform()
        except RuntimeError as e:
            return Response({"error": str(e), "code": 503}, status=status.HTTP_503_SERVICE_UNAVAILABLE)
        if MODEL is None:
            return Response({
                "error": "缺素识别模型未加载",
                "code": 503
            }, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        predicted_class, err = self._run_recognition(image)

        if err:
            return Response({"error": err, "code": 503}, status=status.HTTP_503_SERVICE_UNAVAILABLE)

        result_text = CLASS_NAMES[predicted_class] if 0 <= predicted_class < len(CLASS_NAMES) else "未知"
        response_data = {"result": result_text, "code": 200}

        if predicted_class == 1:
            deficiency = NutrientDeficiency.objects.create(
                parcel=field,
                nutrient_type='K',
                intensity=0.5
            )
            fer_region, fer_err = self._create_fer_region_for_deficiency(field, 'K', 0.5)
            if fer_region:
                fer_region.deficiencies.add(deficiency)
                response_data["fer_region"] = FerRegionSerializer(fer_region).data
                response_data["message"] = "已检测到缺钾，已记录缺素并生成追肥建议"
            else:
                response_data["message"] = "已记录缺钾缺素，追肥记录创建失败"

        return Response(response_data, status=status.HTTP_200_OK)
