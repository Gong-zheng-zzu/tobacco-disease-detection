from django.db import transaction
from django.db.models import Sum
from django.utils import timezone
from django.utils.dateparse import parse_date
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import CuringBatch, HarvestBatch, LandParcel, QualityInspection
from .roles import SecureAPIView
from ..security import active_role


def envelope(data, msg='操作成功', code=200):
    return {'code': code, 'msg': msg, 'data': data}


def query_params(request, queryset, date_field):
    status_value = request.query_params.get('status')
    parcel_id = request.query_params.get('parcel_id')
    date_from = parse_date(request.query_params.get('date_from', '')) if request.query_params.get('date_from') else None
    date_to = parse_date(request.query_params.get('date_to', '')) if request.query_params.get('date_to') else None
    if status_value:
        queryset = queryset.filter(status=status_value)
    if parcel_id and hasattr(queryset.model, 'parcel_id'):
        queryset = queryset.filter(parcel_id=parcel_id)
    if date_from:
        queryset = queryset.filter(**{f'{date_field}__date__gte' if 'time' in date_field else f'{date_field}__gte': date_from})
    if date_to:
        queryset = queryset.filter(**{f'{date_field}__date__lte' if 'time' in date_field else f'{date_field}__lte': date_to})
    return queryset


class WorkspaceSummaryView(SecureAPIView):
    def get(self, request):
        role = active_role(request)
        is_admin = role == 'admin'
        harvest = HarvestBatch.objects.all() if is_admin else HarvestBatch.objects.filter(operator=request.user)
        curing = CuringBatch.objects.all() if is_admin else CuringBatch.objects.filter(operator=request.user)
        quality = QualityInspection.objects.all() if is_admin else QualityInspection.objects.filter(inspector=request.user)
        if role == 'harvest':
            metrics = [
                {'label': '待入库批次', 'value': harvest.filter(status='pending').count(), 'hint': '等待称重确认'},
                {'label': '今日鲜重', 'value': harvest.filter(harvest_date=timezone.now().date()).aggregate(v=Sum('fresh_weight'))['v'] or 0, 'hint': '以现场称重为准'},
                {'label': '已送烘烤', 'value': harvest.filter(status='sent_to_curing').count(), 'hint': '可追踪批次'},
            ]
        elif role == 'curing':
            metrics = [
                {'label': '进行中烤房', 'value': curing.filter(status='running').count(), 'hint': '需要记录温湿度'},
                {'label': '当前异常', 'value': curing.filter(status='abnormal').count(), 'hint': '需要及时处理'},
                {'label': '已完成批次', 'value': curing.filter(status='complete').count(), 'hint': '本账号记录'},
            ]
        elif role == 'quality':
            metrics = [
                {'label': '待质检', 'value': quality.filter(status='pending').count(), 'hint': '等待入场检验'},
                {'label': '今日称重', 'value': quality.filter(inspected_at__date=timezone.now().date()).aggregate(v=Sum('weight'))['v'] or 0, 'hint': '以现场称重为准'},
                {'label': '需复检', 'value': quality.filter(status='recheck').count(), 'hint': '待复核处理'},
            ]
        elif role == 'admin':
            from ..models import User, Role, Device
            metrics = [
                {'label': '用户数', 'value': User.objects.count(), 'hint': '进入管理查看'},
                {'label': '启用角色', 'value': Role.objects.count(), 'hint': '角色配置'},
                {'label': '在线设备', 'value': Device.objects.filter(status='在线').count(), 'hint': '设备状态'},
            ]
        else:
            metrics = [
                {'label': '采收批次', 'value': harvest.count(), 'hint': '关联地块批次'},
                {'label': '烘烤批次', 'value': curing.count(), 'hint': '批次流转'},
                {'label': '质检记录', 'value': quality.count(), 'hint': '质量追溯'},
            ]
        return Response(envelope({'role': role, 'metrics': metrics, 'demo': True,
                                  'recent': list(harvest.order_by('-harvest_date').values('batch_no', 'status')[:5])}))


class HarvestBatchView(SecureAPIView):
    def get(self, request):
        base = HarvestBatch.objects.all() if active_role(request) == 'admin' else HarvestBatch.objects.filter(operator=request.user)
        queryset = query_params(request, base.select_related('parcel'), 'harvest_date')
        page = max(int(request.query_params.get('page', 1)), 1)
        page_size = min(max(int(request.query_params.get('page_size', 20)), 1), 100)
        total = queryset.count()
        items = list(queryset[(page - 1) * page_size:page * page_size].values(
            'id', 'batch_no', 'parcel_id', 'parcel__name', 'harvest_date', 'growth_stage',
            'leaf_position', 'fresh_weight', 'status', 'notes'))
        return Response(envelope({'items': items, 'page': page, 'page_size': page_size, 'total': total}))

    def post(self, request):
        parcel = LandParcel.objects.filter(id=request.data.get('parcel_id'), user=request.user).first()
        if not parcel:
            return Response(envelope({}, '地块不存在或不属于当前用户', 400), status=400)
        required = ['batch_no', 'harvest_date', 'fresh_weight']
        if any(request.data.get(item) in (None, '') for item in required):
            return Response(envelope({}, '批次号、采收日期和鲜重不能为空', 400), status=400)
        batch = HarvestBatch.objects.create(
            parcel=parcel, operator=request.user, batch_no=request.data['batch_no'],
            harvest_date=request.data['harvest_date'], growth_stage=request.data.get('growth_stage', '成熟期'),
            leaf_position=request.data.get('leaf_position', ''), fresh_weight=request.data['fresh_weight'],
            status=request.data.get('status', 'pending'), notes=request.data.get('notes', ''),
        )
        return Response(envelope({'id': batch.id, 'batch_no': batch.batch_no}), status=201)


class CuringBatchView(SecureAPIView):
    def get(self, request):
        queryset = (CuringBatch.objects.all() if active_role(request) == 'admin' else CuringBatch.objects.filter(operator=request.user)).select_related('harvest_batch')
        if request.query_params.get('status'):
            queryset = queryset.filter(status=request.query_params['status'])
        items = list(queryset.values('id', 'batch_no', 'harvest_batch_id', 'barn_name', 'loaded_at', 'stage', 'status', 'temperature', 'humidity', 'loss_weight'))
        return Response(envelope({'items': items, 'total': len(items)}))

    def post(self, request):
        harvest = HarvestBatch.objects.filter(id=request.data.get('harvest_batch_id'), operator=request.user).first()
        if not harvest:
            return Response(envelope({}, '采收批次不存在或无权访问', 400), status=400)
        batch = CuringBatch.objects.create(
            harvest_batch=harvest, operator=request.user, batch_no=request.data['batch_no'],
            barn_name=request.data['barn_name'], loaded_at=request.data.get('loaded_at'),
            stage=request.data.get('stage', 'yellowing'), status=request.data.get('status', 'planned'),
            temperature=request.data.get('temperature'), humidity=request.data.get('humidity'),
            notes=request.data.get('notes', ''),
        )
        harvest.status = 'sent_to_curing'
        harvest.save(update_fields=['status'])
        return Response(envelope({'id': batch.id, 'batch_no': batch.batch_no}), status=201)


class QualityInspectionView(SecureAPIView):
    def get(self, request):
        queryset = (QualityInspection.objects.all() if active_role(request) == 'admin' else QualityInspection.objects.filter(inspector=request.user)).select_related('harvest_batch')
        if request.query_params.get('status'):
            queryset = queryset.filter(status=request.query_params['status'])
        items = list(queryset.values('id', 'purchase_no', 'harvest_batch_id', 'inspected_at', 'weight', 'grade', 'moisture', 'appearance', 'impurity_weight', 'status', 'notes'))
        return Response(envelope({'items': items, 'total': len(items)}))

    def post(self, request):
        harvest = HarvestBatch.objects.filter(id=request.data.get('harvest_batch_id')).first()
        if not harvest:
            return Response(envelope({}, '采收批次不存在', 400), status=400)
        inspection = QualityInspection.objects.create(
            harvest_batch=harvest, inspector=request.user, purchase_no=request.data['purchase_no'],
            weight=request.data.get('weight', 0), grade=request.data.get('grade', ''),
            moisture=request.data.get('moisture'), appearance=request.data.get('appearance', ''),
            impurity_weight=request.data.get('impurity_weight', 0), status=request.data.get('status', 'pending'),
            notes=request.data.get('notes', ''),
        )
        return Response(envelope({'id': inspection.id, 'purchase_no': inspection.purchase_no}), status=201)
