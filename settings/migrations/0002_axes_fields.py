from django.db import migrations, models

class Migration(migrations.Migration):
    dependencies = [
        ('settings', '0001_initial'),
    ]

    operations = [
        migrations.AddField(
            model_name='sitesettings',
            name='axes_failure_limit',
            field=models.PositiveIntegerField(default=5, help_text='Tentativas máximas antes do bloqueio'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='axes_cooloff_time',
            field=models.PositiveIntegerField(default=1, help_text='Tempo de bloqueio (em horas)'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='axes_lock_out_at_failure',
            field=models.BooleanField(default=True, help_text='Bloquear imediatamente ao atingir o limite'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='axes_use_user_agent',
            field=models.BooleanField(default=True, help_text='Diferenciar tentativas por user-agent'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='axes_only_user_failure',
            field=models.BooleanField(default=False, help_text='Bloquear apenas por usuário, não por IP'),
        ),
        migrations.AddField(
            model_name='sitesettings',
            name='axes_reset_on_success',
            field=models.BooleanField(default=True, help_text='Resetar contador ao login bem-sucedido'),
        ),
    ]
