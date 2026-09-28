from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.test import TestCase
from django.urls import reverse

from .models import User


class RegistrationSecurityTests(TestCase):
    def setUp(self):
        cache.clear()

    def register(self, username='grower1', phone='13912345678', password='Tobacco2026!'):
        captcha = self.client.get(reverse('captcha')).json()['data']
        return self.client.post(reverse('register'), {
            'username': username, 'phone': phone,
            'password1': password, 'password2': password,
            'captcha_id': captcha['captcha_id'],
            'captcha_code': cache.get('captcha:' + captcha['captcha_id']),
        })

    def test_rejects_weak_password_and_invalid_phone(self):
        for password in ('123456', 'onlyletters', '123456789012'):
            self.assertEqual(self.register(password=password).json()['code'], 400)
        self.assertEqual(self.register(phone='123').json()['code'], 400)
        self.assertFalse(User.objects.exists())

    def test_registers_with_hash_and_logs_in(self):
        self.assertEqual(self.register().json()['code'], 200)
        user = User.objects.get(username='grower1')
        self.assertNotEqual(user.password, 'Tobacco2026!')
        self.assertTrue(check_password('Tobacco2026!', user.password))
        captcha = self.client.get(reverse('captcha')).json()['data']
        self.assertEqual(self.client.post(reverse('login'), {
            'username': 'grower1', 'password': 'Tobacco2026!',
            'captcha_id': captcha['captcha_id'],
            'captcha_code': cache.get('captcha:' + captcha['captcha_id']),
        }).json()['code'], 200)
        self.assertEqual(self.register().json()['code'], 400)

    def test_old_plaintext_password_is_upgraded_after_login(self):
        user = User.objects.create(username='legacy', phone='13800138000', password='123456')
        captcha = self.client.get(reverse('captcha')).json()['data']
        response = self.client.post(reverse('login'), {
            'username': 'legacy', 'password': '123456',
            'captcha_id': captcha['captcha_id'],
            'captcha_code': cache.get('captcha:' + captcha['captcha_id']),
        })
        self.assertEqual(response.json()['code'], 200)
        user.refresh_from_db()
        self.assertTrue(check_password('123456', user.password))

    def test_register_throttle_and_user_creation_bypass(self):
        for _ in range(5):
            self.assertEqual(self.register(password='weak').status_code, 200)
        self.assertEqual(self.register(password='weak').status_code, 429)
        self.assertEqual(self.client.post(reverse('user_list'), {
            'username': 'bypass', 'phone': '13912345679',
        }).status_code, 401)
        self.assertFalse(User.objects.exists())

    def test_user_list_and_other_user_are_private(self):
        user = User.objects.create(username='legacy', phone='13800138000', password='123456')
        self.assertEqual(self.client.get(reverse('user_list')).status_code, 401)
        self.assertEqual(self.client.get(reverse('user_detail', args=[user.id])).status_code, 401)
