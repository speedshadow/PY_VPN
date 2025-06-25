from django import forms
from .models import SiteSettings

from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile

class SiteSettingsForm(forms.ModelForm):
    def clean_favicon(self):
        favicon = self.cleaned_data.get('favicon')
        if not favicon:
            return favicon
        ext = favicon.name.split('.')[-1].lower()
        if ext not in ['png', 'ico']:
            raise forms.ValidationError('O favicon deve ser um arquivo PNG ou ICO.')
        # Redimensiona se necessário
        try:
            img = Image.open(favicon)
            if img.format.lower() not in ['png', 'ico']:
                raise forms.ValidationError('O favicon deve ser um arquivo PNG ou ICO.')
            # Se maior que 64x64, redimensiona
            max_size = 64
            if img.width > max_size or img.height > max_size:
                img = img.resize((max_size, max_size), Image.LANCZOS)
                thumb_io = BytesIO()
                # Salva no mesmo formato
                img_format = 'PNG' if ext == 'png' else 'ICO'
                img.save(thumb_io, format=img_format)
                new_favicon = InMemoryUploadedFile(
                    thumb_io, None, favicon.name, favicon.content_type, thumb_io.tell(), None
                )
                return new_favicon
        except Exception:
            raise forms.ValidationError('Erro ao processar o favicon. Envie um arquivo PNG ou ICO válido.')
        return favicon

    class Meta:
        model = SiteSettings
        fields = [
            'site_name', 'site_url', 'contact_email',
            'favicon',
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
