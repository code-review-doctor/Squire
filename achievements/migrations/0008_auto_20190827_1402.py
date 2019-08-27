# Generated by Django 2.2.3 on 2019-08-27 12:02

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('achievements', '0007_auto_20190827_1332'),
    ]

    operations = [
        migrations.AlterField(
            model_name='achievement',
            name='category',
            field=models.ForeignKey(blank=True, default=1, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='related_achievements', to='achievements.Category'),
        ),
    ]
