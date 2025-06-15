from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.conf import settings
from .models import SiteSettings

@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin):
    list_display = ('site_name', 'site_url', 'maintenance_mode', 'security_status', 'created_at')
    list_editable = ('maintenance_mode',)
    readonly_fields = ('created_at', 'updated_at', 'security_status_display')
    
    # Agrupa as configurações em abas
    fieldsets = (
        ('Informações Básicas', {
            'fields': (
                'site_name', 'site_url', 'contact_email',
            )
        }),
        ('Configurações de SEO', {
            'fields': (
                'seo_title', 'seo_description', 'seo_keywords',
                'google_analytics_id', 'google_site_verification'
            )
        }),
        ('Configurações de Manutenção', {
            'fields': (
                'maintenance_mode', 'maintenance_message'
            )
        }),
        ('Segurança - HTTPS e Cabeçalhos', {
            'fields': (
                'enable_https', 'enable_hsts', 'hsts_max_age',
                'enable_xss_filter', 'enable_content_type_nosniff',
                'enable_x_frame_options', 'x_frame_options'
            )
        }),
        ('Configurações de Sessão', {
            'fields': (
                'session_cookie_secure', 'session_cookie_http_only',
                'session_cookie_samesite', 'csrf_cookie_secure',
                'csrf_cookie_http_only'
            )
        }),
        ('Segurança de Senhas', {
            'fields': (
                'enable_2fa', 'password_min_length',
                'password_require_uppercase', 'password_require_lowercase',
                'password_require_number', 'password_require_special_char'
            )
        }),
        ('Proteção contra Ataques', {
            'fields': (
                'axes_failure_limit', 'axes_cooloff_time',
                'axes_lock_out_at_failure', 'axes_use_user_agent',
                'axes_only_user_failure', 'axes_reset_on_success'
            )
        }),
        ('Status de Segurança', {
            'fields': ('security_status_display',)
        }),
        ('Metadados', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at')
        }),
    )
    
    def get_fieldsets(self, request, obj=None):
        if not obj:
            return self.add_fieldsets
        return super().get_fieldsets(request, obj)
    
    def get_readonly_fields(self, request, obj=None):
        if obj:  # editing an existing object
            return self.readonly_fields + ('security_status_display',)
        return self.readonly_fields
    
    def security_status(self, obj):
        status = obj.get_security_status()
        html = []
        for key, value in status.items():
            icon = '✅' if value else '❌'
            html.append(f"<div>{icon} {key.replace('_', ' ').title()}</div>")
        return format_html(''.join(html))
    security_status.short_description = 'Status de Segurança'
    security_status.allow_tags = True
    
    def security_status_display(self, obj):
        return self.security_status(obj)
    security_status_display.short_description = 'Resumo de Segurança'
    security_status_display.allow_tags = True
    
    def has_add_permission(self, request):
        # Permite apenas uma instância
        return not SiteSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Não permite deletar as configurações
        return False
    
    def response_add(self, request, obj, post_url_continue=None):
        response = super().response_add(request, obj, post_url_continue)
        # Aplica as configurações após salvar
        obj.apply_security_settings()
        return response
    
    def response_change(self, request, obj):
        response = super().response_change(request, obj)
        # Aplica as configurações após atualizar
        obj.apply_security_settings()
        return response
    
    class Media:
        css = {
            'all': ('admin/css/security_status.css',)
        }
        js = ('admin/js/security_settings.js',)
