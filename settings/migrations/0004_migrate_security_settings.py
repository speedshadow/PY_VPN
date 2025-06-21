from django.db import migrations

def migrate_security_settings(apps, schema_editor):
    """Migra as configurações de segurança existentes para o novo modelo"""
    SiteSettings = apps.get_model('settings', 'SiteSettings')
    
    # Tenta obter as configurações existentes
    try:
        settings = SiteSettings.objects.first()
        if not settings:
            return
            
        # Se existirem configurações antigas no security_settings, migre-as
        if hasattr(settings, 'security_settings') and settings.security_settings:
            security_settings = settings.security_settings
            
            # Mapeia as configurações antigas para os novos campos
            field_mapping = {
                'enable_https': 'enable_https',
                'enable_hsts': 'enable_hsts',
                'hsts_max_age': 'hsts_max_age',
                'enable_xss_filter': 'enable_xss_filter',
                'enable_content_type_nosniff': 'enable_content_type_nosniff',
                'enable_x_frame_options': 'enable_x_frame_options',
                'x_frame_options': 'x_frame_options',
                'session_cookie_secure': 'session_cookie_secure',
                'session_cookie_http_only': 'session_cookie_http_only',
                'session_cookie_samesite': 'session_cookie_samesite',
                'csrf_cookie_secure': 'csrf_cookie_secure',
                'csrf_cookie_http_only': 'csrf_cookie_http_only',
            }
            
            # Atualiza os campos com os valores antigos
            for old_field, new_field in field_mapping.items():
                if old_field in security_settings and hasattr(settings, new_field):
                    setattr(settings, new_field, security_settings[old_field])
            
            # Salva as alterações
            settings.save()
            
    except Exception as e:
        print(f"Erro ao migrar configurações de segurança: {e}")

class Migration(migrations.Migration):

    dependencies = [
        ('settings', '0003_alter_sitesettings_options_and_more'),
    ]

    operations = [
        migrations.RunPython(migrate_security_settings, reverse_code=migrations.RunPython.noop),
    ]
