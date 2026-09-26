"""
Django 管理命令：生成样例数据
用法: python manage.py generate_sample_data
"""
from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import timedelta
from decimal import Decimal

from app2.models import User, LandParcel, NutrientDeficiency, Fer_record, Fer_region_record, Device


class Command(BaseCommand):
    help = '生成缺素、施肥等样例数据，供数据分析、缺素识别等页面展示'

    def handle(self, *args, **options):
        user, _ = User.objects.get_or_create(
            id=1,
            defaults={'username': 'admin', 'password': '123456', 'phone': '13800138000'}
        )
        parcels = list(LandParcel.objects.filter(user=user).order_by('id'))
        if not parcels:
            for i, (name, area) in enumerate([('1号地块', 1500.5), ('2号地块', 800.0), ('3号地块', 1100.0),
                                              ('4号地块', 950.0), ('5号地块', 680.0)], 1):
                # name 必须在查找条件里：否则 5 次循环都会匹配到第一条记录，只生成 1 个地块
                LandParcel.objects.get_or_create(user=user, name=name, defaults={'area': area})
            parcels = list(LandParcel.objects.filter(user=user).order_by('id'))

        now = timezone.now()
        created = 0

        # 为每个地块生成多日期的缺素记录
        for parcel in parcels[:5]:
            for day_ago, types in [
                (28, [('N', 0.52), ('P', 0.38)]),
                (21, [('N', 0.48), ('K', 0.55)]),
                (14, [('P', 0.42), ('N', 0.35)]),
                (7, [('K', 0.60), ('P', 0.50)]),
                (3, [('N', 0.40)]),
                (0, [('K', 0.45)]),
            ]:
                dt = now - timedelta(days=day_ago)
                for nutrient_type, intensity in types:
                    obj = NutrientDeficiency.objects.create(
                        parcel=parcel,
                        nutrient_type=nutrient_type,
                        intensity=Decimal(str(intensity)),
                    )
                    NutrientDeficiency.objects.filter(pk=obj.pk).update(created_at=dt)
                    created += 1

        # 为每个地块生成设备
        device_templates = [
            ('土壤湿度传感器', '传感器'),
            ('空气温湿度传感器', '传感器'),
            ('多光谱相机', '传感器'),
            ('植保无人机', '无人机'),
            ('灌溉执行器', '执行器'),
        ]
        device_created = 0
        for parcel in parcels[:5]:
            for i, (name, dev_type) in enumerate(device_templates):
                _, was_created = Device.objects.get_or_create(
                    user=user,
                    field=parcel,
                    name=f'{parcel.name}-{name}',
                    defaults={'type': dev_type, 'status': '在线'}
                )
                if was_created:
                    device_created += 1

        self.stdout.write(self.style.SUCCESS(f'已生成 {created} 条缺素记录'))
        if device_created:
            self.stdout.write(self.style.SUCCESS(f'已生成 {device_created} 个设备（分布于各地块）'))
