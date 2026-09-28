from django.core.cache import cache
from django.test import TestCase

from .models import HarvestBatch, LandParcel, Role, User, UserRole


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
