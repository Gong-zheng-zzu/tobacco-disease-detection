# 移除地理位置相关字段，精简数据库

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('app2', '0010_alter_fer_region_record_fer_geometry_and_more'),
    ]

    operations = [
        # LandParcel: 添加 name，移除 geometry/longitude/latitude
        migrations.AddField(
            model_name='landparcel',
            name='name',
            field=models.CharField(default='未命名地块', max_length=64, verbose_name='地块名称'),
            preserve_default=False,
        ),
        migrations.RemoveField(
            model_name='landparcel',
            name='geometry',
        ),
        migrations.RemoveField(
            model_name='landparcel',
            name='longitude',
        ),
        migrations.RemoveField(
            model_name='landparcel',
            name='latitude',
        ),
        # NutrientDeficiency: 移除 deficiency_geometry
        migrations.RemoveField(
            model_name='nutrientdeficiency',
            name='deficiency_geometry',
        ),
        # Fer_region_record: 移除 fer_geometry
        migrations.RemoveField(
            model_name='fer_region_record',
            name='fer_geometry',
        ),
        # Fer_record: 移除 fer_location
        migrations.RemoveField(
            model_name='fer_record',
            name='fer_location',
        ),
    ]
