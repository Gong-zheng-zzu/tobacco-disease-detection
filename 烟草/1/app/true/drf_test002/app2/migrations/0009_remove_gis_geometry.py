# 将 GeoDjango 几何字段改为 TextField，不再依赖 GDAL/PostGIS

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("app2", "0008_fer_region_record"),
    ]

    operations = [
        migrations.RemoveField(model_name="landparcel", name="geometry"),
        migrations.AddField(
            model_name="landparcel",
            name="geometry",
            field=models.TextField(blank=True, null=True),
        ),
        migrations.RemoveField(model_name="nutrientdeficiency", name="deficiency_geometry"),
        migrations.AddField(
            model_name="nutrientdeficiency",
            name="deficiency_geometry",
            field=models.TextField(default=""),
        ),
        migrations.RemoveField(model_name="fer_region_record", name="fer_geometry"),
        migrations.AddField(
            model_name="fer_region_record",
            name="fer_geometry",
            field=models.TextField(default="", verbose_name="施肥区域几何信息"),
        ),
    ]
