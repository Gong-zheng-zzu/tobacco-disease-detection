from rest_framework import serializers
from django.db import models
from django.utils import timezone
from .models import *
from datetime import datetime


class UserRegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, max_length=128)

    class Meta:
        model = User
        fields = ['username', 'phone', 'password']


class UserLoginSerializer(serializers.Serializer):
    username = serializers.CharField(max_length=16)
    password = serializers.CharField(write_only=True)


class UserDetailSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ['username', 'phone', 'field_count', 'device_count']


class LandParcelSerializer(serializers.ModelSerializer):
    class Meta:
        model = LandParcel
        fields = ['id', 'user', 'name', 'area', 'field_type']
        read_only_fields = ['id']


class FerCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fer_record
        fields = ['field_id', 'growth_stage']

    def validate_field_id(self, value):
        if not Fer_record._meta.get_field('field_id').related_model.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("指定的地块不存在")
        return value

    def validate_growth_stage(self, value):
        valid_stages = [choice[0] for choice in Fer_record.CHOICES_STAGES]
        if value not in valid_stages:
            raise serializers.ValidationError(f"无效的生长阶段，必须是 {valid_stages} 之一")
        return value

    def create(self, validated_data):
        field_id = validated_data['field_id']
        max_fer_num = Fer_record.objects.filter(field_id=field_id).aggregate(
            models.Max('fer_num')
        )['fer_num__max'] or 0
        validated_data['fer_num'] = max_fer_num + 1
        return Fer_record.objects.create(**validated_data)


class FerDetailSerializer(serializers.ModelSerializer):
    field_id = serializers.PrimaryKeyRelatedField(
        queryset=Fer_record._meta.get_field('field_id').related_model.objects.all(),
        source='field_id.id'
    )
    growth_stage_display = serializers.CharField(source='get_growth_stage_display', read_only=True)
    fer_time = serializers.SerializerMethodField()

    class Meta:
        model = Fer_record
        fields = [
            'id', 'field_id', 'fer_num', 'growth_stage', 'growth_stage_display',
            'fer_time', 'base_n_used', 'base_p_used', 'base_k_used', 'base_s_used', 'notes'
        ]

    def get_fer_time(self, obj):
        if obj.fer_time:
            try:
                dt = timezone.localtime(obj.fer_time)
                return dt.strftime('%Y年%m月%d日  %H:%M')
            except (ValueError, TypeError):
                pass
        return None


class PesticideCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Pesticide_record
        fields = ['field_id', 'pesticide_name', 'dosage', 'unit', 'target_pest', 'notes']

    def validate_field_id(self, value):
        if not LandParcel.objects.filter(id=value.id).exists():
            raise serializers.ValidationError("指定的地块不存在")
        return value

    def create(self, validated_data):
        field_id = validated_data['field_id']
        max_num = Pesticide_record.objects.filter(field_id=field_id).aggregate(
            models.Max('record_num')
        )['record_num__max'] or 0
        validated_data['record_num'] = max_num + 1
        return Pesticide_record.objects.create(**validated_data)


class PesticideDetailSerializer(serializers.ModelSerializer):
    field_id = serializers.PrimaryKeyRelatedField(
        queryset=LandParcel.objects.all(),
        source='field_id.id'
    )
    spray_time = serializers.SerializerMethodField()

    class Meta:
        model = Pesticide_record
        fields = [
            'id', 'field_id', 'record_num', 'spray_time',
            'pesticide_name', 'dosage', 'unit', 'target_pest', 'notes'
        ]

    def get_spray_time(self, obj):
        if obj.spray_time:
            try:
                dt = timezone.localtime(obj.spray_time)
                return dt.strftime('%Y年%m月%d日  %H:%M')
            except (ValueError, TypeError):
                pass
        return None


class NDSerializer(serializers.ModelSerializer):
    nutrient_type_display = serializers.CharField(source='get_nutrient_type_display', read_only=True)
    created_at_date = serializers.SerializerMethodField()
    parcel_id = serializers.IntegerField(read_only=True)

    class Meta:
        model = NutrientDeficiency
        fields = ['id', 'parcel_id', 'nutrient_type', 'nutrient_type_display', 'intensity',
                  'verification_source', 'verification_reference', 'created_at', 'created_at_date']

    def get_created_at_date(self, obj):
        if isinstance(obj.created_at, datetime):
            return obj.created_at.date().strftime('%Y-%m-%d')
        return None


class FerRegionCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Fer_region_record
        fields = ['parcel']


class DeviceSerializer(serializers.ModelSerializer):
    field_id = serializers.PrimaryKeyRelatedField(
        queryset=LandParcel.objects.all(),
        source='field',
        allow_null=True,
        required=False
    )

    class Meta:
        model = Device
        fields = ['id', 'user', 'name', 'type', 'status', 'field_id']


class FerRegionSerializer(serializers.ModelSerializer):
    combined_nutrient_type = serializers.ReadOnlyField()
    fer_time = serializers.SerializerMethodField()

    class Meta:
        model = Fer_region_record
        fields = ['id', 'parcel', 'extra_n_used', 'extra_p_used', 'extra_k_used',
                  'combined_nutrient_type', 'fer_time']

    def get_fer_time(self, obj):
        if obj.fer_time:
            try:
                dt = timezone.localtime(obj.fer_time)
                return dt.strftime('%Y年%m月%d日 %H:%M')
            except (ValueError, TypeError):
                pass
        return None
