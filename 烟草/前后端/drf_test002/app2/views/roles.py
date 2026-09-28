from django.db import transaction
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Role, User, UserRole
from ..security import BusinessPermission, LegacyTokenAuthentication, active_role


ROLE_CODES = {'grower', 'plant_protection', 'harvest', 'curing', 'quality', 'admin'}


class SecureAPIView(APIView):
    authentication_classes = [LegacyTokenAuthentication]
    permission_classes = [BusinessPermission]


def role_data(user):
    memberships = list(UserRole.objects.filter(user=user).select_related('role').order_by('-is_primary', 'role__code'))
    return {
        'user_id': user.id,
        'username': user.username,
        'roles': [{'code': item.role.code, 'name': item.role.name, 'description': item.role.description,
                   'is_primary': item.is_primary} for item in memberships],
        'primary_role': next((item.role.code for item in memberships if item.is_primary), memberships[0].role.code if memberships else None),
    }


class MeView(SecureAPIView):
    def get(self, request):
        return Response({'code': 200, 'msg': '查询成功', 'data': role_data(request.user)})


class ActiveRoleView(SecureAPIView):
    def post(self, request):
        requested = str(request.data.get('role', '')).strip()
        assigned = set(request.user.user_roles.values_list('role__code', flat=True))
        if requested not in assigned:
            return Response({'code': 403, 'msg': 'role not assigned', 'data': {}}, status=403)
        data = role_data(request.user)
        data['active_role'] = requested
        return Response({'code': 200, 'msg': 'role switched', 'data': data})


class RoleListView(SecureAPIView):
    def get(self, request):
        roles = Role.objects.all().values('code', 'name', 'description')
        return Response({'code': 200, 'msg': '查询成功', 'data': list(roles)})


class UserRoleView(SecureAPIView):
    def post(self, request, user_id):
        user = User.objects.filter(pk=user_id).first()
        if not user:
            return Response({'code': 404, 'msg': '用户不存在'}, status=404)
        codes = request.data.get('roles', [])
        primary = request.data.get('primary_role')
        if not isinstance(codes, list) or not codes or not set(codes).issubset(ROLE_CODES):
            return Response({'code': 400, 'msg': '角色列表无效'}, status=400)
        if primary not in codes:
            primary = codes[0]
        with transaction.atomic():
            UserRole.objects.filter(user=user).delete()
            role_map = {role.code: role for role in Role.objects.filter(code__in=codes)}
            for code in codes:
                UserRole.objects.create(user=user, role=role_map[code], is_primary=code == primary)
        return Response({'code': 200, 'msg': '角色更新成功', 'data': role_data(user)})

    def delete(self, request, user_id, role_code):
        membership = UserRole.objects.filter(user_id=user_id, role__code=role_code).first()
        if not membership:
            return Response({'code': 404, 'msg': '角色不存在'}, status=404)
        if membership.role.code == 'admin' and UserRole.objects.filter(role__code='admin').count() <= 1:
            return Response({'code': 400, 'msg': '至少保留一个管理员'}, status=400)
        membership.delete()
        return Response({'code': 200, 'msg': '角色已撤销'})


class AdminUsersView(SecureAPIView):
    def get(self, request):
        users = User.objects.all().order_by('id')
        data = []
        for user in users:
            item = role_data(user)
            item['phone'] = user.phone
            data.append(item)
        return Response({'code': 200, 'msg': '查询成功', 'data': data})
