from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import User, LandParcel, NutrientDeficiency
from ..serializer import NDSerializer


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
