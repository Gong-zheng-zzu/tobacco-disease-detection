from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import User, LandParcel, NutrientDeficiency
from ..serializer import NDSerializer


class ConfirmedDeficiencyView(APIView):
    """Store a reviewed nutrient finding with traceable evidence, not a photo guess."""
    authentication_classes = []
    permission_classes = []

    def post(self, request, user_id, fieldnum):
        user = User.objects.filter(pk=user_id).first()
        field = LandParcel.objects.filter(user_id=user_id, pk=fieldnum).first()
        if user is None or field is None:
            return Response({"error": "用户或地块不存在"}, status=status.HTTP_404_NOT_FOUND)
        if not user.token or request.headers.get("X-User-Token") != user.token:
            return Response({"error": "请重新登录后提交"}, status=status.HTTP_403_FORBIDDEN)

        nutrient = str(request.data.get("nutrient_type", "")).upper()
        source = str(request.data.get("verification_source", ""))
        reference = str(request.data.get("verification_reference", "")).strip()
        if nutrient not in {"N", "P", "K"}:
            return Response({"error": "请选择缺氮、缺磷或缺钾"}, status=status.HTTP_400_BAD_REQUEST)
        if source not in {"lab_report", "expert_review"} or not reference or len(reference) > 256:
            return Response({"error": "请选择依据类型并填写报告编号或复核人及日期"}, status=status.HTTP_400_BAD_REQUEST)

        record = NutrientDeficiency.objects.create(
            parcel=field,
            nutrient_type=nutrient,
            intensity=None,
            verification_source=source,
            verification_reference=reference,
        )
        return Response({"code": 200, "data": NDSerializer(record).data,
                         "message": "已保存确认结果；施肥用量仍需根据检测数值和农艺方案确定"},
                        status=status.HTTP_201_CREATED)


class ParcelDeficiencyView(APIView):
    """按地块查询缺素记录"""
    authentication_classes = []
    permission_classes = []

    def get(self, request, user_id, fieldnum):
        try:
            user = User.objects.get(pk=user_id)
            field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
            if not field:
                return Response({"msg": "不存在该地块", "code": 400}, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400}, status=status.HTTP_400_BAD_REQUEST)

        records = NutrientDeficiency.objects.filter(parcel=field).order_by('created_at')
        data = NDSerializer(records, many=True).data
        return Response({"msg": "查询成功", "code": 200, "data": data})


class UserAllDeficienciesView(APIView):
    """查询用户全部地块的缺素记录集合"""
    authentication_classes = []
    permission_classes = []

    def get(self, request, user_id):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400}, status=status.HTTP_400_BAD_REQUEST)

        parcels = LandParcel.objects.filter(user_id=user.id).values_list('id', flat=True)
        records = NutrientDeficiency.objects.filter(parcel_id__in=parcels).order_by('created_at')
        data = NDSerializer(records, many=True).data
        return Response({"msg": "查询成功", "code": 200, "data": data})
