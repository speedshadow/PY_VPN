# Generated by Django 5.2.3 on 2025-06-15 14:15

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('vpn', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='vpn',
            name='is_active',
            field=models.BooleanField(default=True),
        ),
    ]
