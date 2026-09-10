from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import LandParcel, User
from ..serializer import LandParcelSerializer
from rest_framework import status

class CreateLandParcelView(APIView):
    def post(self, request, user_id):
        try:
            # 检查用户是否存在
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"msg": "用户不存在", "code": 404}, status=status.HTTP_404_NOT_FOUND)

        # 获取请求数据
        data = request.data.copy()
        data['user'] = user_id  # 将 user_id 添加到数据中

        # 序列化并保存地块
        serializer = LandParcelSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "地块创建成功", "code": 200, "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"msg": "数据无效", "code": 400, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

class ListLandParcelsView(APIView):
    def get(self, request, user_id):
        try:
            # 检查用户是否存在
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"msg": "用户不存在", "code": 404}, status=status.HTTP_404_NOT_FOUND)

        # 获取该用户的所有地块
        parcels = LandParcel.objects.filter(user_id=user_id).order_by('id')
        serializer = LandParcelSerializer(parcels, many=True)
        return Response({"msg": "查询成功", "code": 200, "data": serializer.data}, status=status.HTTP_200_OK)

class DeleteLandParcelView(APIView):
    def delete(self, request, user_id, parcel_id):
        try:
            # 检查用户是否存在
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"msg": "用户不存在", "code": 404}, status=status.HTTP_404_NOT_FOUND)

        try:
            # 检查地块是否存在且属于该用户
            parcel = LandParcel.objects.get(id=parcel_id, user_id=user_id)
            parcel.delete()
            return Response({"msg": "地块删除成功", "code": 200, "parcel_id": parcel_id}, status=status.HTTP_200_OK)
        except LandParcel.DoesNotExist:
            return Response({"msg": "地块不存在或不属于该用户", "code": 404}, status=status.HTTP_404_NOT_FOUND)






