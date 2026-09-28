from django.core.validators import MaxValueValidator, MinValueValidator
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [("app2", "0015_pesticide_record")]

    operations = [
        migrations.AlterField(
            model_name="nutrientdeficiency",
            name="intensity",
            field=models.DecimalField(blank=True, decimal_places=2, default=0.5,
                                      max_digits=3, null=True,
                                      validators=[MinValueValidator(0), MaxValueValidator(1)]),
        ),
        migrations.AddField(
            model_name="nutrientdeficiency",
            name="verification_source",
            field=models.CharField(blank=True, default="", max_length=24),
        ),
        migrations.AddField(
            model_name="nutrientdeficiency",
            name="verification_reference",
            field=models.CharField(blank=True, default="", max_length=256),
        ),
    ]
