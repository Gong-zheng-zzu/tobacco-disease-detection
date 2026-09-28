from django.core.cache import cache
from django.test import TestCase

from .models import HarvestBatch, LandParcel, Pesticide_record, Role, User, UserRole


class RoleWorkflowTests(TestCase):
    def setUp(self):
        cache.clear()
        self.user = User.objects.create(username='operator', password='legacy', phone='13900000001')
        self.parcel = LandParcel.objects.create(user=self.user, name='测试地块', area=100)
        role = Role.objects.get(code='harvest')
        UserRole.objects.create(user=self.user, role=role, is_primary=True)
        captcha = self.client.get('/api/auth/captcha/').json()['data']
        response = self.client.post('/api/login/', {
            'username': 'operator', 'password': 'legacy',
            'captcha_id': captcha['captcha_id'],
            'captcha_code': cache.get('captcha:' + captcha['captcha_id']),
        })
        self.auth = {'HTTP_AUTHORIZATION': 'Bearer ' + response.json()['token']}

    def test_me_and_harvest_workflow(self):
        me = self.client.get('/api/me/', **self.auth)
        self.assertEqual(me.status_code, 200)
        self.assertEqual(me.json()['data']['primary_role'], 'harvest')
        created = self.client.post('/api/harvest/batches/', {
            'batch_no': 'ROLE-H-001', 'parcel_id': self.parcel.id,
            'harvest_date': '2026-09-28', 'fresh_weight': '12.50',
        }, **self.auth)
        self.assertEqual(created.status_code, 201)
        self.assertEqual(HarvestBatch.objects.count(), 1)

    def test_wrong_role_is_forbidden(self):
        self.assertEqual(self.client.get('/api/quality/inspections/', **self.auth).status_code, 403)

    def test_unauthenticated_batch_request_is_rejected(self):
        self.assertEqual(self.client.get('/api/harvest/batches/').status_code, 401)

    def test_summary_uses_active_role_records_and_chinese_status(self):
        UserRole.objects.create(user=self.user, role=Role.objects.get(code='plant_protection'))
        Pesticide_record.objects.create(field_id=self.parcel, record_num=1,
                                        pesticide_name='待农技人员确认', target_pest='野火病')
        HarvestBatch.objects.create(parcel=self.parcel, operator=self.user,
                                    batch_no='ROLE-H-002', harvest_date='2026-09-28', fresh_weight=12)

        protection = self.client.get('/api/workspace/summary/', HTTP_X_ACTIVE_ROLE='plant_protection', **self.auth)
        self.assertEqual(protection.status_code, 200)
        data = protection.json()['data']
        self.assertEqual([item['label'] for item in data['metrics']],
                         ['病虫害相关记录', '农药登记', '待人工确认'])
        self.assertEqual([item['value'] for item in data['metrics']], [1, 1, 1])
        self.assertEqual(data['recent'][0]['label'], '野火病')

        harvest = self.client.get('/api/workspace/summary/', **self.auth)
        self.assertEqual(harvest.status_code, 200)
        self.assertEqual(harvest.json()['data']['recent'][0]['status_label'], '待入库')
