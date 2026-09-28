from secrets import compare_digest

from django.core.cache import cache
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed, PermissionDenied
from rest_framework.permissions import BasePermission

from .models import User

ROLE_CODES = {'grower', 'plant_protection', 'harvest', 'curing', 'quality', 'admin'}


def client_ip(request):
    forwarded = request.META.get('HTTP_X_FORWARDED_FOR', '')
    return forwarded.split(',')[-1].strip() if forwarded else request.META.get('REMOTE_ADDR', '')


def token_user(request):
    header = request.META.get('HTTP_AUTHORIZATION', '')
    token = header[7:].strip() if header.startswith('Bearer ') else request.META.get('HTTP_X_USER_TOKEN', '').strip()
    if not token:
        return None
    user = User.objects.filter(token=token).first()
    if user and user.token and compare_digest(user.token, token):
        return user
    return None


def active_role(request, user=None):
    user = user or (request.user if isinstance(request.user, User) else None)
    if user is None:
        return None
    requested = request.META.get('HTTP_X_ACTIVE_ROLE', '').strip()
    assigned = set(user.user_roles.values_list('role__code', flat=True))
    if requested and requested in assigned:
        return requested
    if requested:
        return None
    primary = user.user_roles.filter(is_primary=True).values_list('role__code', flat=True).first()
    return primary or next(iter(assigned), None)


class LegacyTokenAuthentication(BaseAuthentication):
    def authenticate(self, request):
        header = request.META.get('HTTP_AUTHORIZATION', '')
        if not header:
            return None
        user = token_user(request)
        if user is None:
            raise AuthenticationFailed('登录已失效，请重新登录')
        return user, user.token

    def authenticate_header(self, request):
        return 'Bearer'


class BusinessPermission(BasePermission):
    PUBLIC = ('/api/auth/captcha/', '/api/login/', '/api/register/', '/api/weather/')

    def has_permission(self, request, view):
        path = request.path
        if path in self.PUBLIC:
            return True
        user = request.user if isinstance(request.user, User) else None
        if user is None:
            raise AuthenticationFailed('请先登录')
        roles = set(user.user_roles.values_list('role__code', flat=True))
        current = active_role(request, user)
        if current is None:
            raise PermissionDenied('当前工作角色无效，请重新选择角色')
        if current == 'admin':
            return True
        if path.startswith('/api/users/') or path == '/api/roles/' or path.startswith('/api/admin/'):
            raise PermissionDenied('需要管理员权限')
        if path == '/api/me/active-role/':
            return True
        if path.startswith('/api/user/'):
            parts = path.split('/')
            if len(parts) > 3 and parts[3].isdigit() and int(parts[3]) != user.id:
                raise PermissionDenied('不能访问其他用户的数据')
        required = None
        if path.startswith('/api/workspace/summary/'):
            required = {current}
        elif path.startswith('/api/harvest/'):
            required = {'harvest', 'curing', 'quality'} if request.method == 'GET' else {'harvest'}
        elif path.startswith('/api/curing/'):
            required = {'curing'}
        elif path.startswith('/api/quality/'):
            required = {'quality'}
        elif path.startswith('/api/user/') and path.endswith('/fields/list/') and request.method == 'GET':
            required = {'grower', 'plant_protection', 'harvest'}
        elif '/pesticide' in path or 'unified_detect' in path:
            required = {'plant_protection', 'grower'}
        elif path not in ('/api/me/', '/api/ai/consult/'):
            required = {'grower', 'plant_protection'}
        if required and current not in required:
            raise PermissionDenied('当前角色无权访问此功能')
        return True


def is_locked(kind, key):
    return bool(cache.get(f'auth-lock:{kind}:{key}'))


def count_failure(kind, key, limit=5, window=900):
    cache_key = f'auth-fail:{kind}:{key}'
    count = cache.get(cache_key, 0) + 1
    cache.set(cache_key, count, window)
    if count >= limit:
        cache.set(f'auth-lock:{kind}:{key}', True, window)


def clear_failures(kind, key):
    cache.delete(f'auth-fail:{kind}:{key}')
    cache.delete(f'auth-lock:{kind}:{key}')
