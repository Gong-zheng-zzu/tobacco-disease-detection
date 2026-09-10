from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import Fer_record, User, LandParcel
from ..serializer import FerCreateSerializer, FerDetailSerializer
import requests


def get_fertilizer_ratio(growth_stage, soil_type, weather_condition):
    soil_type_map = {1: "高肥力", 2: "中肥力", 3: "低肥力"}
    soil_type_str = soil_type_map.get(soil_type, "中肥力")

    # 基础配比
    if soil_type_str == "高肥力":
        n_p_k_ratio = (1.0, 1.2, 0.5)
    elif soil_type_str == "低肥力":
        n_p_k_ratio = (1.2, 1.0, 0.7)
    elif soil_type_str == "中肥力":
        n_p_k_ratio = (1.1, 1.1, 0.6)

    # 生长阶段调整配比和总量因子（基于每亩总需求）
    if growth_stage == 1:  # 苗期：N 1.5–2kg, P 1.6–2kg, K 3–4kg
        n_p_k_ratio = (1.75, 1.8, 3.5)
        volume_factor = 0.8
    elif growth_stage == 2:  # 还苗期：N 0.5–1kg, P 0.4–0.6kg, K 1–1.6kg
        n_p_k_ratio = (0.75, 0.5, 1.3)
        volume_factor = 0.4
    elif growth_stage == 3:  # 伸根期：N 1.5–2kg, P 2–3kg, K 4–6kg
        n_p_k_ratio = (1.75, 2.5, 5.0)
        volume_factor = 1.0
    elif growth_stage == 4:  # 旺长期：N 3–4kg, P 4–5kg, K 8–12kg
        n_p_k_ratio = (3.5, 4.5, 10.0)
        volume_factor = 1.4
    elif growth_stage == 5:  # 成熟期：N 0, P 1–2kg, K 4–6kg
        n_p_k_ratio = (0, 1.5, 5.0)
        volume_factor = 0.7

    # 天气条件调整
    if weather_condition == "降雨":
        n_p_k_ratio = tuple(x * 0.8 for x in n_p_k_ratio)
        volume_factor *= 0.9  # 降雨减少 10% 总量
    elif weather_condition == "晴朗":
        n_p_k_ratio = tuple(x * 1.1 for x in n_p_k_ratio)
        volume_factor *= 1.1  # 晴朗增加 10% 总量

    return n_p_k_ratio, volume_factor

def get_weather_condition():
    api_url = "https://devapi.qweather.com/v7/weather/now"
    api_key = "fe6c2f9fd34645a1b398fb7bfda343e8"
    location = "101180101"  # 郑州的地区ID
    request_url = f"{api_url}?key={api_key}&location={location}"
    response = requests.get(request_url)

    if response.status_code == 200:
        weather_data = response.json()
        weather_condition = weather_data['now']['text']
        return weather_condition
    else:
        print("无法获取天气预报数据，请检查API密钥和网络连接。")
        return "未知"


class FerView(APIView):
    # 获取某个地块的所有施肥记录，按时间降序排列
    def get(self, request, user_id, fieldnum):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400})

        try:
            field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
            if not field:
                return Response({"msg": "不存在该地块", "code": 400})
        except LandParcel.DoesNotExist:
            return Response({"msg": "不存在该地块", "code": 400})

        fer_records = Fer_record.objects.filter(field_id=field.id).order_by('-fer_time')
        serializer = FerDetailSerializer(fer_records, many=True)
        return Response({"msg": "查询成功", "code": 200, "data": serializer.data})

    def post(self, request, user_id, fieldnum):
        try:
            user = User.objects.get(pk=user_id)
            field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
            if not field:
                return Response({"msg": "不存在该地块", "code": 400})
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400})

        data = {"field_id": field.id, "growth_stage": request.data.get("growth_stage")}
        serializer = FerCreateSerializer(data=data)
        if not serializer.is_valid():
            return Response({"msg": "数据无效", "code": 400, "errors": serializer.errors})

        # 计算肥料量
        weather_condition = get_weather_condition() or "多云"  # 默认值
        n_p_k_ratio, volume_factor = get_fertilizer_ratio(data["growth_stage"], field.field_type, weather_condition)
        base_spray_volume = field.area / (2000 / 3) * 75
        total_spray_volume = base_spray_volume * volume_factor
        ratio_sum = sum(n_p_k_ratio)

        if ratio_sum == 0:
            return Response({"msg": "肥料配比计算错误", "code": 500})

        n_volume = total_spray_volume * n_p_k_ratio[0] / ratio_sum
        p_volume = total_spray_volume * n_p_k_ratio[1] / ratio_sum
        k_volume = total_spray_volume * n_p_k_ratio[2] / ratio_sum

        # 保存记录
        fer_record = serializer.save()
        fer_record.base_n_used = n_volume
        fer_record.base_p_used = p_volume
        fer_record.base_k_used = k_volume
        fer_record.base_s_used = total_spray_volume
        fer_record.save()

        # 使用详细序列化器返回更新后的数据
        response_serializer = FerDetailSerializer(fer_record)
        return Response({"msg": "施肥记录已创建", "code": 200, "data": response_serializer.data})

    # 删除施肥记录
    def delete(self, request, user_id, fieldnum, fernum):
        try:
            user = User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400})

        try:
            field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
            if not field:
                return Response({"msg": "不存在该地块", "code": 400})
        except LandParcel.DoesNotExist:
            return Response({"msg": "不存在该地块", "code": 400})

        try:
            fer_record = Fer_record.objects.filter(field_id=field.id, fer_num=fernum).first()
            if not fer_record:
                return Response({"msg": "不存在该记录", "code": 400})
            fer_record.delete()
            return Response({"msg": "删除成功", "code": 200})
        except Fer_record.DoesNotExist:
            return Response({"msg": "不存在该记录", "code": 400})