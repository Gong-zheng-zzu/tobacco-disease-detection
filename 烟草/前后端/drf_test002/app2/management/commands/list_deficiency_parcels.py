"""
查看缺素记录对应的地块 id，以及地块列表。
用法: python manage.py list_deficiency_parcels
说明: parcel_id 存的是 app2_landparcel 表的主键 id，不是「几号地块」的名称。
      若你只有 5 个地块但看到 parcel_id=9，说明库里存在 id=9 的地块（可能曾删过地块，主键不会回收）。
"""
from django.core.management.base import BaseCommand
from django.db.models import Count

from app2.models import LandParcel, NutrientDeficiency


class Command(BaseCommand):
    help = '列出地块 id/名称 及缺素记录数，便于核对 parcel_id'

    def handle(self, *args, **options):
        self.stdout.write('===== 地块列表 (id 即 parcel_id) =====')
        for p in LandParcel.objects.order_by('id').values('id', 'name', 'area', 'user_id'):
            self.stdout.write(f"  id={p['id']}  name={p['name']!r}  area={p['area']}  user_id={p['user_id']}")

        self.stdout.write('')
        self.stdout.write('===== 缺素记录按 parcel_id 统计 =====')
        qs = NutrientDeficiency.objects.values('parcel_id').annotate(cnt=Count('id')).order_by('parcel_id')
        for row in qs:
            self.stdout.write(f"  parcel_id={row['parcel_id']}  缺素记录数={row['cnt']}")

        self.stdout.write('')
        self.stdout.write('说明: 缺素表里的 parcel_id 对应上面地块的 id，不是「1号地块」里的数字。')
