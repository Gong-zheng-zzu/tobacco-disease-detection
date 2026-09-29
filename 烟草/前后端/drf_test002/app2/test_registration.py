from django.contrib.auth.hashers import check_password
from django.core.cache import cache
from django.core import mail
from django.test import TestCase, override_settings
from django.urls import reverse

from .models import User
from .views.user import email_code_key


@override_settings(EMAIL_BACKEND='django.core.mail.backends.locmem.EmailBackend',
                   EMAIL_HOST_USER='sender@qq.com', EMAIL_HOST_PASSWORD='test-only')
class RegistrationSecurityTests(TestCase):
    def setUp(self):
        cache.clear()

    def register(self, username='grower1', phone='13912345678', password='Tobacco2026!', email='grower@example.com', code=None):
        captcha = self.client.get(reverse('captcha')).json()['data']
        if code is None:
            code = '123456'
            cache.set(email_code_key(email), code, 300)
        return self.client.post(reverse('register'), {
            'username': username, 'phone': phone, 'email': email, 'email_code': code,
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
        self.assertEqual(user.email, 'grower@example.com')
        self.assertIsNone(cache.get(email_code_key(user.email)))
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

    def test_email_code_send_and_reuse(self):
        captcha = self.client.get(reverse('captcha')).json()['data']
        payload = {'email': 'Grower@Example.com', 'captcha_id': captcha['captcha_id'],
                   'captcha_code': cache.get('captcha:' + captcha['captcha_id'])}
        response = self.client.post(reverse('email-code'), payload)
        self.assertEqual(response.json()['code'], 200)
        self.assertEqual(len(mail.outbox), 1)
        self.assertIn(cache.get(email_code_key('grower@example.com')), mail.outbox[0].body)
        self.assertEqual(self.client.post(reverse('email-code'), payload).json()['code'], 400)
        sent_code = cache.get(email_code_key('grower@example.com'))
        self.assertEqual(self.register(code=sent_code).json()['code'], 200)
        self.assertEqual(self.register(username='grower2', phone='13912345679').json()['code'], 400)

    def test_email_code_required_and_expired(self):
        captcha = self.client.get(reverse('captcha')).json()['data']
        response = self.client.post(reverse('register'), {
            'username': 'grower1', 'phone': '13912345678', 'email': 'grower@example.com',
            'password1': 'Tobacco2026!', 'password2': 'Tobacco2026!',
            'captcha_id': captcha['captcha_id'], 'captcha_code': cache.get('captcha:' + captcha['captcha_id']),
        })
        self.assertEqual(response.json()['code'], 400)
        self.assertFalse(User.objects.exists())

    def test_wrong_email_code_does_not_create_user(self):
        cache.set(email_code_key('grower@example.com'), '654321', 300)
        self.assertEqual(self.register(code='000000').json()['code'], 400)
        self.assertFalse(User.objects.exists())

    @override_settings(EMAIL_HOST_PASSWORD='')
    def test_mail_unavailable_does_not_issue_code(self):
        captcha = self.client.get(reverse('captcha')).json()['data']
        response = self.client.post(reverse('email-code'), {
            'email': 'grower@example.com', 'captcha_id': captcha['captcha_id'],
            'captcha_code': cache.get('captcha:' + captcha['captcha_id']),
        })
        self.assertEqual(response.status_code, 503)
        self.assertIsNone(cache.get(email_code_key('grower@example.com')))

    def test_user_list_and_other_user_are_private(self):
        user = User.objects.create(username='legacy', phone='13800138000', password='123456')
        self.assertEqual(self.client.get(reverse('user_list')).status_code, 401)
        self.assertEqual(self.client.get(reverse('user_detail', args=[user.id])).status_code, 401)
