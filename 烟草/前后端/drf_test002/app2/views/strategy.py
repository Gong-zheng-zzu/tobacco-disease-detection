from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import LandParcel, NutrientDeficiency, Pesticide_record


class FieldStrategyContextView(APIView):
    """Return the latest field context used by the Android strategy page."""

    def get(self, request, user_id, fieldnum):
        field = LandParcel.objects.filter(user_id=user_id, id=fieldnum).first()
        if field is None:
            return Response(
                {"msg": "不存在该地块", "code": 400},
                status=status.HTTP_400_BAD_REQUEST,
            )

        deficiencies = NutrientDeficiency.objects.filter(parcel=field).order_by("-created_at")
        diseases = (
            Pesticide_record.objects.filter(field_id=field.id)
            .exclude(target_pest__isnull=True)
            .exclude(target_pest="")
            .order_by("-spray_time")
        )

        deficiency_types = list(dict.fromkeys(item.nutrient_type for item in deficiencies))[:3]
        disease_types = list(dict.fromkeys(item.target_pest for item in diseases))[:5]
        latest_deficiency = deficiencies.first()
        latest_disease = diseases.first()

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
                "latest_deficiency_at": latest_deficiency.created_at if latest_deficiency else None,
                "latest_disease_at": latest_disease.spray_time if latest_disease else None,
            },
        })
