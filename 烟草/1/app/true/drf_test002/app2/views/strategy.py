from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status

from ..models import User, LandParcel, NutrientDeficiency, Pesticide_record


class FieldStrategyContextView(APIView):
    """按地块返回策略页所需上下文（面积、缺素结果、病虫害结果）"""
    authentication_classes = []
    permission_classes = []

    def get(self, request, user_id, fieldnum):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400}, status=status.HTTP_400_BAD_REQUEST)

        field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
        if not field:
            return Response({"msg": "不存在该地块", "code": 400}, status=status.HTTP_400_BAD_REQUEST)

        deficiencies_qs = NutrientDeficiency.objects.filter(parcel=field).order_by("-created_at")
        deficiency_types = []
        for item in deficiencies_qs:
            if item.nutrient_type not in deficiency_types:
                deficiency_types.append(item.nutrient_type)
            if len(deficiency_types) >= 3:
                break

        diseases_qs = Pesticide_record.objects.filter(
            field_id=field.id
        ).exclude(
            target_pest__isnull=True
        ).exclude(
            target_pest=""
        ).order_by("-spray_time")
        disease_types = []
        for item in diseases_qs:
            if item.target_pest not in disease_types:
                disease_types.append(item.target_pest)
            if len(disease_types) >= 5:
                break

        latest_deficiency_at = deficiencies_qs.first().created_at if deficiencies_qs.exists() else None
        latest_disease_at = diseases_qs.first().spray_time if diseases_qs.exists() else None

        return Response({
            "msg": "查询成功",
            "code": 200,
            "data": {
                "field": {
                    "id": field.id,
                    "name": field.name,
                    "area": float(field.area or 0),
                    "field_type": field.field_type,
                },
                "deficiency_types": deficiency_types,
                "disease_types": disease_types,
                "latest_deficiency_at": latest_deficiency_at,
                "latest_disease_at": latest_disease_at,
            }
        }, status=status.HTTP_200_OK)
