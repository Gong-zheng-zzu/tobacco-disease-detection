from django.db import migrations, models
import django.db.models.deletion


ROLES = [
    ('grower', '种植端', '地块、生育期、营养和农事作业'),
    ('plant_protection', '植保端', '病虫害识别、防治和农药记录'),
    ('harvest', '采叶/采收端', '采收批次和鲜烟叶入库'),
    ('curing', '烘烤端', '烤房、烘烤阶段和异常记录'),
    ('quality', '收购/质检端', '称重、分级和质量检查'),
    ('admin', '管理员端', '用户、角色、配置和审计'),
]


def seed_roles(apps, schema_editor):
    Role = apps.get_model('app2', 'Role')
    for code, name, description in ROLES:
        Role.objects.update_or_create(code=code, defaults={'name': name, 'description': description})
    User = apps.get_model('app2', 'User')
    UserRole = apps.get_model('app2', 'UserRole')
    admin = User.objects.filter(username='admin').first()
    admin_role = Role.objects.filter(code='admin').first()
    if admin and admin_role:
        UserRole.objects.get_or_create(user=admin, role=admin_role, defaults={'is_primary': True})


class Migration(migrations.Migration):
    dependencies = [('app2', '0017_alter_user_password')]

    operations = [
        migrations.CreateModel(
            name='Role',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('code', models.CharField(max_length=32, unique=True)),
                ('name', models.CharField(max_length=64)),
                ('description', models.CharField(blank=True, default='', max_length=256)),
            ],
            options={'db_table': 'app2_role', 'ordering': ['code']},
        ),
        migrations.CreateModel(
            name='UserRole',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_primary', models.BooleanField(default=False)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('role', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_roles', to='app2.role')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='user_roles', to='app2.user')),
            ],
            options={'db_table': 'app2_user_role'},
        ),
        migrations.AddConstraint(
            model_name='userrole',
            constraint=models.UniqueConstraint(fields=('user', 'role'), name='unique_user_role'),
        ),
        migrations.CreateModel(
            name='HarvestBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_no', models.CharField(max_length=40, unique=True)),
                ('harvest_date', models.DateField()),
                ('growth_stage', models.CharField(default='成熟期', max_length=32)),
                ('leaf_position', models.CharField(blank=True, default='', max_length=64)),
                ('fresh_weight', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('pending', '待入库'), ('stored', '已入库'), ('sent_to_curing', '已送烘烤')], default='pending', max_length=24)),
                ('image', models.ImageField(blank=True, null=True, upload_to='harvest/%Y/%m/%d/')),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('operator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='harvest_batches', to='app2.user')),
                ('parcel', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='harvest_batches', to='app2.landparcel')),
            ],
            options={'db_table': 'app2_harvest_batch', 'ordering': ['-harvest_date', '-id']},
        ),
        migrations.CreateModel(
            name='CuringBatch',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('batch_no', models.CharField(max_length=40, unique=True)),
                ('barn_name', models.CharField(max_length=64)),
                ('loaded_at', models.DateTimeField(blank=True, null=True)),
                ('stage', models.CharField(choices=[('yellowing', '变黄'), ('color_fixing', '定色'), ('stem_drying', '干筋'), ('complete', '已完成')], default='yellowing', max_length=24)),
                ('status', models.CharField(choices=[('planned', '待开始'), ('running', '进行中'), ('complete', '已完成'), ('abnormal', '异常')], default='planned', max_length=24)),
                ('temperature', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('humidity', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('loss_weight', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('notes', models.TextField(blank=True, default='')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('harvest_batch', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='curing_batches', to='app2.harvestbatch')),
                ('operator', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='curing_batches', to='app2.user')),
            ],
            options={'db_table': 'app2_curing_batch', 'ordering': ['-created_at']},
        ),
        migrations.CreateModel(
            name='QualityInspection',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('purchase_no', models.CharField(max_length=40, unique=True)),
                ('inspected_at', models.DateTimeField(auto_now_add=True)),
                ('weight', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('grade', models.CharField(blank=True, default='', max_length=32)),
                ('moisture', models.DecimalField(blank=True, decimal_places=2, max_digits=5, null=True)),
                ('appearance', models.CharField(blank=True, default='', max_length=128)),
                ('impurity_weight', models.DecimalField(decimal_places=2, default=0, max_digits=10)),
                ('status', models.CharField(choices=[('pending', '待质检'), ('passed', '已通过'), ('recheck', '需复检')], default='pending', max_length=24)),
                ('image', models.ImageField(blank=True, null=True, upload_to='quality/%Y/%m/%d/')),
                ('notes', models.TextField(blank=True, default='')),
                ('harvest_batch', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='quality_inspections', to='app2.harvestbatch')),
                ('inspector', models.ForeignKey(on_delete=django.db.models.deletion.PROTECT, related_name='quality_inspections', to='app2.user')),
            ],
            options={'db_table': 'app2_quality_inspection', 'ordering': ['-inspected_at']},
        ),
        migrations.RunPython(seed_roles, migrations.RunPython.noop),
    ]
