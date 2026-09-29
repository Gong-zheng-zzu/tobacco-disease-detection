from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [('app2', '0019_curingbatch_is_demo_harvestbatch_is_demo_and_more')]

    operations = [
        migrations.AddField(
            model_name='user',
            name='email',
            field=models.EmailField(blank=True, max_length=254, null=True, unique=True, verbose_name='邮箱'),
        ),
    ]
