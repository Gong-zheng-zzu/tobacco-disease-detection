from decimal import Decimal
from django.db.models import Max
from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Pesticide_record, User, LandParcel
from ..serializer import PesticideCreateSerializer, PesticideDetailSerializer

# 1 亩 = 2000/3 平方米，与前端一致
MU_M2 = 2000 / 3
# 病害种类对应的农药与每亩用量（与 Pesticide.vue 的 DISEASE_CONFIG 一致）
DISEASE_CONFIG = {
    "白星病": {"pesticide_name": "50% 多菌灵可湿性粉剂", "per_mu": 100, "unit": "克"},
    "黄叶病": {"pesticide_name": "99% 磷酸二氢钾", "per_mu": 100, "unit": "克"},
    "烟青虫": {"pesticide_name": "4.5% 高效氯氰菊酯乳油", "per_mu": 30, "unit": "毫升"},
    "叶厚病": {
        "pesticide_name": "硼肥+磷酸二氢钾",
        "unit": "克",
        "parts": [
            {"name": "硼肥", "per_mu_min": 20, "per_mu_max": 30, "unit": "克"},
            {"name": "磷酸二氢钾", "per_mu": 100, "unit": "克"},
        ],
    },
}


def _calc_yehoubing_dosage(area_m2):
    """叶厚病：硼肥 20～30 克/亩 + 磷酸二氢钾 100 克/亩，返回 (dosage, notes)。"""
    cfg = DISEASE_CONFIG["叶厚病"]
    if not cfg.get("parts") or not area_m2:
        return Decimal("0"), ""
    mu = float(area_m2) / MU_M2
    boron = cfg["parts"][0]
    phosph = cfg["parts"][1]
    b_min = round(mu * boron["per_mu_min"] * 10) / 10
    b_max = round(mu * boron["per_mu_max"] * 10) / 10
    p_val = round(mu * phosph["per_mu"] * 10) / 10
    notes = f"{b_min}～{b_max} {boron['unit']}+{p_val} {phosph['unit']}"
    return Decimal(str(p_val)), notes


def _create_pesticide_record_for_disease(field, disease_type):
    """根据病害类型和地块面积创建一条农药记录，返回创建的记录或 None。"""
    area = float(field.area or 0)
    if area <= 0:
        return None
    cfg = DISEASE_CONFIG.get(disease_type)
    if not cfg:
        return None
    mu = area / MU_M2
    if cfg.get("parts"):
        dosage, notes = _calc_yehoubing_dosage(area)
        pesticide_name = cfg["pesticide_name"]
        unit = cfg["unit"]
    else:
        per_mu = cfg["per_mu"]
        dosage = Decimal(str(round(mu * per_mu * 100) / 100))
        unit = cfg["unit"]
        notes = ""
        pesticide_name = cfg["pesticide_name"]
    max_num = (
        Pesticide_record.objects.filter(field_id=field.id).aggregate(
            max_num=Max("record_num")
        )["max_num"]
        or 0
    )
    record = Pesticide_record.objects.create(
        field_id=field,
        record_num=max_num + 1,
        pesticide_name=pesticide_name,
        dosage=dosage,
        unit=unit,
        target_pest=disease_type,
        notes=notes or "",
    )
    return record


class PesticideView(APIView):
    """农药记录：按地块查询、新建、删除"""

    def get(self, request, user_id, fieldnum):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400})

        field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
        if not field:
            return Response({"msg": "不存在该地块", "code": 400})

        records = Pesticide_record.objects.filter(field_id=field.id).order_by('-spray_time')
        serializer = PesticideDetailSerializer(records, many=True)
        return Response({"msg": "查询成功", "code": 200, "data": serializer.data})

    def post(self, request, user_id, fieldnum):
        try:
            user = User.objects.get(pk=user_id)
            field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
            if not field:
                return Response({"msg": "不存在该地块", "code": 400})
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400})

        data = {
            "field_id": field.id,
            "pesticide_name": request.data.get("pesticide_name", ""),
            "dosage": request.data.get("dosage", 0),
            "unit": request.data.get("unit", "ml"),
            "target_pest": request.data.get("target_pest") or "",
            "notes": request.data.get("notes") or "",
        }
        serializer = PesticideCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response({"msg": "数据无效", "code": 400, "errors": serializer.errors})

        record = serializer.save()
        response_serializer = PesticideDetailSerializer(record)
        return Response({"msg": "农药记录已创建", "code": 200, "data": response_serializer.data})

    def delete(self, request, user_id, fieldnum, recordnum):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400})

        field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
        if not field:
            return Response({"msg": "不存在该地块", "code": 400})

        record = Pesticide_record.objects.filter(field_id=field.id, record_num=recordnum).first()
        if not record:
            return Response({"msg": "不存在该记录", "code": 400})
        record.delete()
        return Response({"msg": "删除成功", "code": 200})


class PesticideFromDiseaseView(APIView):
    """根据病虫害检测结果（病害种类列表）为指定地块自动添加农药记录"""

    def post(self, request, user_id, fieldnum):
        try:
            user = User.objects.get(pk=user_id)
            field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
            if not field:
                return Response({"msg": "不存在该地块", "code": 400})
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400})

        disease_types = request.data.get("disease_types") or []
        if not isinstance(disease_types, list):
            disease_types = [disease_types] if disease_types else []
        allowed = set(DISEASE_CONFIG.keys())
        to_create = [d for d in disease_types if d in allowed]
        created = 0
        for disease_type in to_create:
            rec = _create_pesticide_record_for_disease(field, disease_type)
            if rec:
                created += 1
        return Response({
            "msg": f"已根据检测结果在农药记录中添加 {created} 条",
            "code": 200,
            "created": created,
            "disease_types": to_create,
        })
