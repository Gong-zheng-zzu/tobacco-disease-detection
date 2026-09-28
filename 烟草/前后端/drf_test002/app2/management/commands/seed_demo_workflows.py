from datetime import date, timedelta
from decimal import Decimal

from django.core.management.base import BaseCommand

from app2.models import CuringBatch, HarvestBatch, LandParcel, QualityInspection, User


class Command(BaseCommand):
    help = 'Create idempotent workflow demo records for the admin account.'

    def handle(self, *args, **options):
        user = User.objects.filter(username='admin').first()
        if not user:
            self.stderr.write('admin user not found')
            return
        parcels = list(LandParcel.objects.filter(user=user).order_by('id')[:3])
        if not parcels:
            self.stderr.write('admin has no parcels')
            return
        today = date.today()
        specs = [
            ('DEMO-H-001', parcels[0], today - timedelta(days=2), Decimal('186.50'), 'pending'),
            ('DEMO-H-002', parcels[min(1, len(parcels) - 1)], today - timedelta(days=5), Decimal('224.00'), 'sent_to_curing'),
            ('DEMO-H-003', parcels[min(2, len(parcels) - 1)], today - timedelta(days=9), Decimal('198.20'), 'stored'),
        ]
        harvests = {}
        for batch_no, parcel, harvest_date, weight, status in specs:
            batch, _ = HarvestBatch.objects.update_or_create(
                batch_no=batch_no,
                defaults={'parcel': parcel, 'harvest_date': harvest_date, 'growth_stage': '成熟期',
                          'leaf_position': '中部叶', 'fresh_weight': weight, 'operator': user,
                          'status': status, 'notes': '界面演示数据，请以现场记录为准', 'is_demo': True},
            )
            harvests[batch_no] = batch
        curing_specs = [
            ('DEMO-C-001', '1号烤房', 'yellowing', 'running', '42.0', '68.0', 'DEMO-H-002'),
            ('DEMO-C-002', '2号烤房', 'stem_drying', 'complete', '55.0', '36.0', 'DEMO-H-003'),
        ]
        for no, barn, stage, status, temp, humidity, harvest_no in curing_specs:
            CuringBatch.objects.update_or_create(
                batch_no=no,
                defaults={'harvest_batch': harvests[harvest_no], 'barn_name': barn, 'stage': stage,
                          'status': status, 'temperature': Decimal(temp), 'humidity': Decimal(humidity),
                          'operator': user, 'notes': '界面演示数据，请以烤房记录为准', 'is_demo': True},
            )
        quality_specs = [
            ('DEMO-Q-001', 'DEMO-H-001', 'pending', '', None),
            ('DEMO-Q-002', 'DEMO-H-002', 'passed', '样例等级，待现场复核', Decimal('12.50')),
            ('DEMO-Q-003', 'DEMO-H-003', 'recheck', '需复检', Decimal('15.20')),
        ]
        for no, harvest_no, status, grade, moisture in quality_specs:
            QualityInspection.objects.update_or_create(
                purchase_no=no,
                defaults={'harvest_batch': harvests[harvest_no], 'weight': harvests[harvest_no].fresh_weight,
                          'grade': grade, 'moisture': moisture, 'appearance': '样例外观记录',
                          'status': status, 'inspector': user, 'notes': '界面演示数据，不构成质检结论', 'is_demo': True},
            )
        self.stdout.write(self.style.SUCCESS('demo workflow data seeded: 3 harvest, 2 curing, 3 quality'))
