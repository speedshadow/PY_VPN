from django import forms
from .models import SiteSettings

class SiteSettingsForm(forms.ModelForm):
    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_url', 'contact_email',
            'seo_title', 'seo_description', 'google_analytics_id',
            'enable_https', 'enable_hsts', 'enable_xss_filter',
            'session_cookie_secure', 'csrf_cookie_secure',
            'maintenance_mode', 'maintenance_message',
            # Adicione outros campos aqui se eles forem adicionados ao template
        ]
        widgets = {
            # Configurações Básicas
            'site_name': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'site_url': forms.URLInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'contact_email': forms.EmailInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            
            # Configurações de SEO
            'seo_title': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'seo_description': forms.Textarea(attrs={'class': 'w-full border rounded px-2 py-1', 'rows': 3}),
            'google_analytics_id': forms.TextInput(attrs={'class': 'w-full border rounded px-2 py-1'}),
            
            # Configurações de Segurança
            'enable_https': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'enable_hsts': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'hsts_max_age': forms.NumberInput(attrs={'class': 'w-full border rounded px-2 py-1', 'min': 0}),
            'enable_xss_filter': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'x_frame_options': forms.Select(attrs={'class': 'w-full border rounded px-2 py-1'}),
            # Configurações de Sessão
            'session_cookie_secure': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'session_cookie_http_only': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'session_cookie_samesite': forms.Select(attrs={'class': 'w-full border rounded px-2 py-1'}),
            'csrf_cookie_secure': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'csrf_cookie_http_only': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'csrf_cookie_samesite': forms.Select(attrs={'class': 'w-full border rounded px-2 py-1'}),
            
            # Configurações de Senha
            'password_min_length': forms.NumberInput(attrs={'class': 'w-full border rounded px-2 py-1', 'min': 1}),
            'password_require_uppercase': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'password_require_lowercase': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'password_require_number': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'password_require_special_char': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            
            # Configurações de Bloqueio de Conta
            'axes_failure_limit': forms.NumberInput(attrs={'class': 'w-full border rounded px-2 py-1', 'min': 1}),
            'axes_cooloff_time': forms.NumberInput(attrs={'class': 'w-full border rounded px-2 py-1', 'min': 1}),
            'axes_lock_out_at_failure': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'axes_use_user_agent': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'axes_only_user_failure': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'axes_reset_on_success': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            
            # Configurações de Manutenção
            'maintenance_mode': forms.CheckboxInput(attrs={'class': 'form-checkbox'}),
            'maintenance_message': forms.Textarea(attrs={'class': 'w-full border rounded px-2 py-1', 'rows': 3}),
        }
