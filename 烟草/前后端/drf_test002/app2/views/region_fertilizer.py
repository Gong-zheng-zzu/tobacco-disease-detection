from rest_framework.views import APIView
from rest_framework.response import Response
from ..models import LandParcel, NutrientDeficiency, Fer_region_record, User
from ..serializer import FerRegionCreateSerializer, FerRegionSerializer


class FerRegionView(APIView):
    def post(self, request, user_id, fieldnum):
        """创建追肥记录，基于最近的缺素信息（无地理位置）"""
        try:
            user = User.objects.get(pk=user_id)
            field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
            if not field:
                return Response({"msg": "不存在该地块", "code": 400})
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400})

        latest_deficiencies = NutrientDeficiency.objects.filter(parcel=field).order_by('-created_at')
        if not latest_deficiencies.exists():
            return Response({"msg": "无近期缺素数据，无需追肥", "code": 404})

        field_area_m2 = float(field.area)
        created_regions = []

        for nutrient_type in ['N', 'P', 'K']:
            nutrient_deficiencies = latest_deficiencies.filter(
                nutrient_type=nutrient_type, intensity__isnull=False
            )
            if nutrient_deficiencies.exists():
                total_area_m2 = field_area_m2 * 0.3
                avg_intensity = float(sum(d.intensity for d in nutrient_deficiencies) / nutrient_deficiencies.count())
                avg_intensity = max(0.0, min(1.0, avg_intensity))
                factor = 0.5 + avg_intensity * 0.5
                base_unit = 2000 / 3
                base_volume = (field_area_m2 / base_unit) * 75
                area_ratio = total_area_m2 / field_area_m2
                extra_volume = base_volume * area_ratio * 0.3 * factor

                extra_n = extra_volume if nutrient_type == 'N' else 0
                extra_p = extra_volume if nutrient_type == 'P' else 0
                extra_k = extra_volume if nutrient_type == 'K' else 0

                fer_region_data = {"parcel": field.id}
                serializer = FerRegionCreateSerializer(data=fer_region_data)
                if serializer.is_valid():
                    fer_region = serializer.save()
                    fer_region.extra_n_used = extra_n
                    fer_region.extra_p_used = extra_p
                    fer_region.extra_k_used = extra_k
                    fer_region.save()
                    fer_region.deficiencies.set(nutrient_deficiencies)
                    created_regions.append(FerRegionSerializer(fer_region).data)
                else:
                    return Response({"msg": "追肥记录创建失败", "code": 400, "errors": serializer.errors})

        if not created_regions:
            return Response({"msg": "缺素记录尚无核定强度，未创建追肥记录", "code": 404})

        return Response({"msg": "追肥记录已创建", "code": 200, "data": created_regions})

    def get(self, request, user_id, fieldnum):
        """查询指定地块的追肥记录"""
        try:
            user = User.objects.get(pk=user_id)
            field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
            if not field:
                return Response({"msg": "不存在该地块", "code": 400})
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400})

        fer_regions = Fer_region_record.objects.filter(parcel=field).order_by('-fer_time')
        result = [FerRegionSerializer(r).data for r in fer_regions]

        return Response({"msg": "查询成功", "code": 200, "data": result})

    def delete(self, request, user_id, fieldnum, region_id=None, **kwargs):
        """删除追肥记录：按 region_id 删除，或按日期范围删除"""
        try:
            user = User.objects.get(pk=user_id)
            field = LandParcel.objects.filter(user_id=user.id, id=fieldnum).first()
            if not field:
                return Response({"msg": "不存在该地块", "code": 400})
        except User.DoesNotExist:
            return Response({"msg": "不存在该用户", "code": 400})

        region_id_param = region_id or kwargs.get('region_id')
        if region_id_param:
            try:
                region = Fer_region_record.objects.get(id=region_id_param, parcel=field)
                region.delete()
                return Response({"msg": "追肥记录已删除", "code": 200})
            except Fer_region_record.DoesNotExist:
                return Response({"msg": "该追肥记录不存在", "code": 404})

        from datetime import datetime, timedelta
        start_date = request.query_params.get('start_date')
        end_date = request.query_params.get('end_date')

        if not start_date and not end_date:
            latest = Fer_region_record.objects.filter(parcel=field).order_by('-fer_time').first()
            if not latest:
                return Response({"msg": "该地块无追肥记录可删除", "code": 404})
            start = datetime.combine(latest.fer_time.date(), datetime.min.time())
            end = datetime.combine(latest.fer_time.date(), datetime.max.time())
        else:
            try:
                start = datetime.strptime(start_date, '%Y-%m-%d')
                end = datetime.strptime(end_date, '%Y-%m-%d') + timedelta(days=1)
            except (ValueError, TypeError):
                return Response({"msg": "日期格式错误，应为 YYYY-MM-DD", "code": 400})

        fer_regions = Fer_region_record.objects.filter(parcel=field, fer_time__gte=start, fer_time__lt=end)
        count = fer_regions.count()
        fer_regions.delete()
        return Response({"msg": f"已删除 {count} 条追肥记录", "code": 200, "data": {"deleted_count": count}})
