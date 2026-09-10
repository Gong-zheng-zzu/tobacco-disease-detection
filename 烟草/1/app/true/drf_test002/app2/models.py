from django.db import models
from django.core.validators import MinValueValidator, MaxValueValidator

class User(models.Model):
    username = models.CharField(max_length=16, verbose_name="用户名")
    password = models.CharField(max_length=16, verbose_name="密码")
    phone = models.CharField(max_length=13, verbose_name="电话号")
    token = models.CharField(max_length=64, verbose_name="TOKEN", null=True, blank=True, db_index=True)
    device_count = models.IntegerField(verbose_name="设备数", default=0)
    field_count = models.IntegerField(verbose_name="地块数", default=0)

    class Meta:
        db_table = "user_tb"

    def __str__(self):
        return self.username


class LandParcel(models.Model):
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        null=True,
        related_name="land_parcels"
    )
    name = models.CharField(max_length=64, verbose_name="地块名称", default="未命名地块")
    area = models.FloatField(null=False, verbose_name="面积")

    choices_level = (
        (1, '高肥力'),
        (2, '中肥力'),
        (3, '低肥力')
    )
    field_type = models.SmallIntegerField(choices=choices_level, default=2, verbose_name="地块土质类型")

    class Meta:
        db_table = "app2_landparcel"

    def __str__(self):
        return f"{self.name}(id={self.id})"


class NutrientDeficiency(models.Model):
    NUTRIENT_CHOICES = [
        ('N', '缺氮'),
        ('P', '缺磷'),
        ('K', '缺钾'),
    ]

    parcel = models.ForeignKey(
        LandParcel,
        on_delete=models.CASCADE,
        null=False
    )
    nutrient_type = models.CharField(max_length=10, choices=NUTRIENT_CHOICES, null=False)
    intensity = models.DecimalField(
        max_digits=3,
        decimal_places=2,
        default=0.5,
        validators=[MinValueValidator(0), MaxValueValidator(1)]
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "app2_nutrientdeficiency"

    def __str__(self):
        return f"{self.nutrient_type} deficiency in parcel {self.parcel_id}"


class Fer_record(models.Model):
    CHOICES_STAGES = (
        (1, '苗期'),
        (2, '还苗期'),
        (3, '伸根期'),
        (4, '旺长期'),
        (5, '成熟期'),
    )

    field_id = models.ForeignKey(
        to='LandParcel',
        verbose_name="地块编号",
        on_delete=models.CASCADE,
    )
    fer_num = models.IntegerField(verbose_name="施肥记录序号", default=0)
    growth_stage = models.SmallIntegerField(choices=CHOICES_STAGES, verbose_name="生长阶段")
    fer_time = models.DateTimeField(verbose_name="施肥时间", auto_now_add=True)
    base_n_used = models.DecimalField(verbose_name="基础氮肥用量", max_digits=10, decimal_places=2, default=0.00)
    base_p_used = models.DecimalField(verbose_name="基础磷肥用量", max_digits=10, decimal_places=2, default=0.00)
    base_k_used = models.DecimalField(verbose_name="基础钾肥用量", max_digits=10, decimal_places=2, default=0.00)
    base_s_used = models.DecimalField(verbose_name="基础总用量", max_digits=10, decimal_places=2, default=0.00)
    notes = models.TextField(verbose_name="备注", blank=True, null=True)

    class Meta:
        db_table = "Fer_detail_tb"
        verbose_name = "施肥记录"
        verbose_name_plural = "施肥记录"
        unique_together = ('field_id', 'fer_num')
        indexes = [models.Index(fields=['field_id', 'fer_time'])]

    def __str__(self):
        return f"{self.field_id} - 施肥记录 {self.fer_num}"


class Pesticide_record(models.Model):
    """农药记录：按地块记录施药时间、农药名称、用量、防治对象等"""
    field_id = models.ForeignKey(
        to='LandParcel',
        verbose_name="地块编号",
        on_delete=models.CASCADE,
    )
    record_num = models.IntegerField(verbose_name="记录序号", default=0)
    spray_time = models.DateTimeField(verbose_name="施药时间", auto_now_add=True)
    pesticide_name = models.CharField(verbose_name="农药名称", max_length=128, default="")
    dosage = models.DecimalField(verbose_name="用量", max_digits=10, decimal_places=2, default=0.00)
    unit = models.CharField(verbose_name="单位", max_length=32, default="ml", blank=True)
    target_pest = models.CharField(verbose_name="防治对象", max_length=128, blank=True, null=True)
    notes = models.TextField(verbose_name="备注", blank=True, null=True)

    class Meta:
        db_table = "pesticide_record_tb"
        verbose_name = "农药记录"
        verbose_name_plural = "农药记录"
        unique_together = ('field_id', 'record_num')
        indexes = [models.Index(fields=['field_id', 'spray_time'])]

    def __str__(self):
        return f"{self.field_id} - 农药记录 {self.record_num}"


class Fer_region_record(models.Model):
    parcel = models.ForeignKey('LandParcel', on_delete=models.CASCADE, verbose_name="地块编号")
    fer_time = models.DateTimeField(verbose_name="追肥时间", auto_now_add=True)
    extra_n_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="额外氮肥用量")
    extra_p_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="额外磷肥用量")
    extra_k_used = models.DecimalField(max_digits=10, decimal_places=2, default=0.00, verbose_name="额外钾肥用量")
    deficiencies = models.ManyToManyField('NutrientDeficiency', blank=True, verbose_name="关联的缺素区域")

    class Meta:
        db_table = "fer_region_record_tb"

    @property
    def combined_nutrient_type(self):
        return ''.join(sorted(set(self.deficiencies.values_list('nutrient_type', flat=True))))


class Device(models.Model):
    TYPE_CHOICES = [
        ('无人机', '无人机'),
        ('传感器', '传感器'),
        ('执行器', '执行器'),
    ]
    STATUS_CHOICES = [
        ('在线', '在线'),
        ('离线', '离线'),
    ]
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='devices')
    field = models.ForeignKey(
        LandParcel,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='devices',
        verbose_name='所属地块'
    )
    name = models.CharField(max_length=64, verbose_name='设备名称')
    type = models.CharField(max_length=32, choices=TYPE_CHOICES, verbose_name='设备类型')
    status = models.CharField(max_length=16, choices=STATUS_CHOICES, default='在线', verbose_name='状态')

    class Meta:
        db_table = "app2_device"

    def __str__(self):
        return f"{self.name}({self.type})"


class PendingImage(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='pending_images')
    image = models.ImageField(upload_to='pending_images/%Y/%m/%d/', max_length=255)
    upload_time = models.DateTimeField(auto_now_add=True)
    processed = models.BooleanField(default=False)
    field = models.ForeignKey(
        'LandParcel',
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='pending_images'
    )

    class Meta:
        verbose_name = "Pending Image"
        verbose_name_plural = "Pending Images"

    def __str__(self):
        return f"Image {self.id} by {self.user} at {self.upload_time}"


class SensorData(models.Model):
    user = models.ForeignKey('User', on_delete=models.CASCADE, related_name='sensor_data')
    flow_rate = models.FloatField()
    total_volume = models.FloatField()
    level = models.FloatField()
    pump_state = models.BooleanField(default=False)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name = "Sensor Data"
        verbose_name_plural = "Sensor Data"

    def __str__(self):
        return f"Data {self.id} at {self.timestamp}"
