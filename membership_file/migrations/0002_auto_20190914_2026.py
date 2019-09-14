# Generated by Django 2.2.3 on 2019-09-14 18:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('membership_file', '0001_initial'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='member',
            name='postal_code',
        ),
        migrations.AddField(
            model_name='member',
            name='educational_institution',
            field=models.CharField(default='TU/e', max_length=255),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name='member',
            name='student_number',
            field=models.CharField(blank=True, max_length=15, null=True, unique=True),
        ),
    ]
