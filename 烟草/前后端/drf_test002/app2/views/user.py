import re
import uuid
from secrets import compare_digest

from django.contrib.auth.hashers import check_password, identify_hasher, make_password
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.db import IntegrityError, transaction
from django.core.cache import cache
from rest_framework.response import Response
from rest_framework.throttling import AnonRateThrottle
from rest_framework.views import APIView

from ..models import User
from ..serializer import UserLoginSerializer, UserRegisterSerializer
from ..security import client_ip, clear_failures, count_failure, is_locked


class RegisterThrottle(AnonRateThrottle):
    scope = 'register'


class LoginThrottle(AnonRateThrottle):
    scope = 'login'


class RegisteryView(APIView):
    throttle_classes = [RegisterThrottle]

    def post(self, request):
        username = request.data.get('username')
        phone = request.data.get('phone')
        password = request.data.get('password1')
        confirmation = request.data.get('password2')
        captcha_id = request.data.get('captcha_id')
        captcha_code = str(request.data.get('captcha_code', '')).strip().upper()

        captcha_key = f'captcha:{captcha_id}'
        expected_captcha = cache.get(captcha_key) if captcha_id else None
        if not expected_captcha or not captcha_code or captcha_code != str(expected_captcha).upper():
            return Response({'msg': '验证码错误或已过期', 'code': 400})
        cache.delete(captcha_key)

        if not isinstance(username, str) or not re.fullmatch(r'[A-Za-z0-9_\u4e00-\u9fff]{3,16}', username):
            return Response({'msg': '用户名须为3至16位中文、字母、数字或下划线', 'code': 400})
        if not isinstance(phone, str) or not re.fullmatch(r'1[3-9]\d{9}', phone):
            return Response({'msg': '请输入有效的11位手机号', 'code': 400})
        if not isinstance(password, str) or not 10 <= len(password) <= 128:
            return Response({'msg': '密码长度须为10至128位', 'code': 400})
        if not re.search(r'[A-Za-z]', password) or not re.search(r'\d', password):
            return Response({'msg': '密码须同时包含字母和数字', 'code': 400})
        if password != confirmation:
            return Response({'msg': '两次密码不一致', 'code': 400})
        if username.lower() in password.lower() or phone in password:
            return Response({'msg': '密码不能包含用户名或手机号', 'code': 400})
        try:
            validate_password(password)
        except ValidationError as exc:
            return Response({'msg': '；'.join(exc.messages), 'code': 400})
        if User.objects.filter(username=username).exists():
            return Response({'msg': '该用户已注册', 'code': 400})
        if User.objects.filter(phone=phone).exists():
            return Response({'msg': '该手机号已用于注册', 'code': 400})

        serializer = UserRegisterSerializer(data={
            'username': username, 'phone': phone, 'password': make_password(password),
        })
        if not serializer.is_valid():
            return Response({'msg': serializer.errors, 'code': 400})
        try:
            with transaction.atomic():
                serializer.save()
        except IntegrityError:
            return Response({'msg': '用户名或手机号已注册', 'code': 400})
        return Response({'msg': '注册成功', 'code': 200})


class LoginView(APIView):
    throttle_classes = [LoginThrottle]

    def post(self, request):
        serializer = UserLoginSerializer(data=request.data)
        captcha_id = request.data.get('captcha_id')
        captcha_code = str(request.data.get('captcha_code', '')).strip().upper()
        captcha_key = f'captcha:{captcha_id}'
        expected_captcha = cache.get(captcha_key) if captcha_id else None
        ip = client_ip(request)
        username_key = str(request.data.get('username', '')).strip().lower()
        if is_locked('ip', ip) or (username_key and is_locked('user', username_key)):
            return Response({'msg': '失败次数过多，请稍后再试', 'code': 429}, status=429)
        if not expected_captcha or not captcha_code or captcha_code != str(expected_captcha).upper():
            count_failure('ip', ip)
            return Response({'msg': '验证码错误或已过期', 'code': 400})
        cache.delete(captcha_key)
        if not serializer.is_valid():
            count_failure('ip', ip)
            return Response({'msg': '用户名或密码错误', 'code': 400})
        username = serializer.validated_data['username']
        password = serializer.validated_data['password']
        user = User.objects.filter(username=username).first()
        if user is None:
            count_failure('ip', ip)
            count_failure('user', username_key)
            return Response({'msg': '用户名或密码错误', 'code': 400})

        try:
            identify_hasher(user.password)
            hashed = True
        except ValueError:
            hashed = False
        valid = check_password(password, user.password) if hashed else compare_digest(password, user.password)
        if not valid:
            count_failure('ip', ip)
            count_failure('user', username_key)
            return Response({'msg': '用户名或密码错误', 'code': 400})

        if not hashed:
            user.password = make_password(password)
        user.token = str(uuid.uuid4())
        user.save(update_fields=['password', 'token'] if not hashed else ['token'])
        clear_failures('ip', ip)
        clear_failures('user', username_key)
        return Response({
            'msg': '登录成功', 'code': 200, 'token': user.token,
            'user_id': user.id, 'username': user.username,
        })


class UserManage(APIView):
    # Legacy user administration must not expose another public registration path.
    def get(self, request, pk=None):
        if pk is None:
            return Response({'msg': '禁止查看用户列表', 'code': 403}, status=403)
        user = User.objects.filter(pk=pk).first()
        token = request.headers.get('Authorization', '').removeprefix('Bearer ').strip()
        if user is None or not token or not user.token or not compare_digest(token, user.token):
            return Response({'msg': '无权访问该用户', 'code': 403}, status=403)
        return Response({'username': user.username, 'phone': user.phone,
                         'field_count': user.field_count, 'device_count': user.device_count})
