from django.db import migrations, models
from django.contrib.auth.hashers import identify_hasher, make_password


def hash_existing_passwords(apps, schema_editor):
    User = apps.get_model('app2', 'User')
    for user in User.objects.all().iterator():
        try:
            identify_hasher(user.password)
        except ValueError:
            user.password = make_password(user.password)
            user.save(update_fields=['password'])


class Migration(migrations.Migration):
    dependencies = [('app2', '0016_nutrientdeficiency_verification')]

    operations = [
        migrations.AlterField(
            model_name='user', name='password',
            field=models.CharField(max_length=128, verbose_name='密码'),
        ),
        migrations.RunPython(hash_existing_passwords, migrations.RunPython.noop),
        migrations.AlterField(
            model_name='user', name='username',
            field=models.CharField(max_length=16, unique=True, verbose_name='用户名'),
        ),
        migrations.AlterField(
            model_name='user', name='phone',
            field=models.CharField(max_length=13, unique=True, verbose_name='电话号'),
        ),
    ]
