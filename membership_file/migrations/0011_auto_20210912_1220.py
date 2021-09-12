# Generated by Django 2.2.24 on 2021-09-12 10:20

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('membership_file', '0010_export_permission'),
    ]

    operations = [
        migrations.AlterField(
            model_name='memberlog',
            name='member',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, to='membership_file.Member'),
        ),
        migrations.AlterField(
            model_name='memberlog',
            name='user',
            field=models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='created_memberlogs', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='memberlogfield',
            name='member_log',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='updated_fields', to='membership_file.MemberLog'),
        ),
    ]
