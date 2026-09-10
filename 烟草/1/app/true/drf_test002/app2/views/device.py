from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from ..models import Device, User
from ..serializer import DeviceSerializer


class DeviceView(APIView):
    """设备列表、创建（支持按地块筛选）"""

    def get(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"msg": "用户不存在", "code": 404}, status=status.HTTP_404_NOT_FOUND)
        devices = Device.objects.filter(user=user).order_by('id')
        field_id = request.query_params.get('field_id')
        if field_id:
            try:
                devices = devices.filter(field_id=int(field_id))
            except (ValueError, TypeError):
                pass
        serializer = DeviceSerializer(devices, many=True)
        return Response({"msg": "查询成功", "code": 200, "data": serializer.data})

    def post(self, request, user_id):
        try:
            user = User.objects.get(id=user_id)
        except User.DoesNotExist:
            return Response({"msg": "用户不存在", "code": 404}, status=status.HTTP_404_NOT_FOUND)
        data = request.data.copy()
        data['user'] = user_id
        # field_id 可为空，表示未分配地块
        if 'field_id' in data and data['field_id'] is None:
            data['field'] = None
        serializer = DeviceSerializer(data=data)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "设备创建成功", "code": 200, "data": serializer.data}, status=status.HTTP_201_CREATED)
        return Response({"msg": "数据无效", "code": 400, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)


class DeviceDetailView(APIView):
    """单个设备：修改、删除、切换状态"""

    def put(self, request, user_id, device_id):
        try:
            user = User.objects.get(id=user_id)
            device = Device.objects.get(id=device_id, user=user)
        except User.DoesNotExist:
            return Response({"msg": "用户不存在", "code": 404}, status=status.HTTP_404_NOT_FOUND)
        except Device.DoesNotExist:
            return Response({"msg": "设备不存在", "code": 404}, status=status.HTTP_404_NOT_FOUND)
        data = request.data.copy()
        data['user'] = user_id
        serializer = DeviceSerializer(device, data=data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({"msg": "修改成功", "code": 200, "data": serializer.data})
        return Response({"msg": "数据无效", "code": 400, "errors": serializer.errors}, status=status.HTTP_400_BAD_REQUEST)

    def delete(self, request, user_id, device_id):
        try:
            user = User.objects.get(id=user_id)
            device = Device.objects.get(id=device_id, user=user)
        except User.DoesNotExist:
            return Response({"msg": "用户不存在", "code": 404}, status=status.HTTP_404_NOT_FOUND)
        except Device.DoesNotExist:
            return Response({"msg": "设备不存在", "code": 404}, status=status.HTTP_404_NOT_FOUND)
        device.delete()
        return Response({"msg": "删除成功", "code": 200})
