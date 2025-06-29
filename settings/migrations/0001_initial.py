# Generated by Django 5.2.3 on 2025-06-13 19:37

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='SiteSettings',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('site_name', models.CharField(max_length=100)),
                ('site_url', models.URLField()),
                ('seo_title', models.CharField(max_length=255)),
                ('seo_description', models.TextField()),
                ('maintenance_mode', models.BooleanField(default=False)),
                ('security_settings', models.JSONField(blank=True, default=dict, null=True)),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('updated_at', models.DateTimeField(auto_now=True)),
            ],
        ),
    ]
