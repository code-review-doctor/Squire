# Generated by Django 2.2.15 on 2021-09-12 19:51

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('activity_calendar', '0011_auto_20210908_2019'),
    ]

    operations = [
        migrations.AddField(
            model_name='participant',
            name='guest_name',
            field=models.CharField(default='', max_length=123),
            preserve_default=False,
        ),
    ]
