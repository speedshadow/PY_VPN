from django import forms
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from colorfield.fields import ColorField
from .models_customization import SiteCustomization, CustomCSS, CustomJavaScript
import os

class SiteCustomizationForm(forms.ModelForm):
    class Meta:
        model = SiteCustomization
        exclude = ['created_at', 'updated_at']
        widgets = {
            'site_slogan': forms.TextInput(attrs={'placeholder': 'Um slogan cativante para seu site'}),
            'font_family': forms.TextInput(attrs={'class': 'font-mono'}),
            'font_size_base': forms.TextInput(attrs={'class': 'w-24'}),
            'header_scripts': forms.Textarea(attrs={'class': 'font-mono text-xs h-32'}),
            'footer_scripts': forms.Textarea(attrs={'class': 'font-mono text-xs h-32'}),
            'custom_css': forms.Textarea(attrs={'class': 'font-mono text-xs h-64'}),
            'maintenance_message': forms.Textarea(attrs={'rows': 3}),
            'contact_address': forms.Textarea(attrs={'rows': 2}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        
        # Adiciona classes Tailwind aos campos
        for field_name, field in self.fields.items():
            if field_name not in ['logo', 'logo_dark', 'logo_footer', 'favicon', 'og_image']:
                if isinstance(field, forms.BooleanField):
                    field.widget.attrs.update({
                        'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded',
                    })
                elif isinstance(field, forms.CharField) and not isinstance(field, forms.ChoiceField):
                    field.widget.attrs.update({
                        'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                    })
                elif isinstance(field, forms.ChoiceField):
                    field.widget.attrs.update({
                        'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                    })
    
    def clean_logo(self):
        return self._clean_image('logo')
    
    def clean_logo_dark(self):
        return self._clean_image('logo_dark')
    
    def clean_logo_footer(self):
        return self._clean_image('logo_footer')
    
    def clean_favicon(self):
        return self._clean_image('favicon', ['.ico', '.png'])
    
    def _clean_image(self, field_name, allowed_extensions=None):
        if allowed_extensions is None:
            allowed_extensions = ['.png', '.jpg', '.jpeg', '.svg']
            
        image = self.cleaned_data.get(field_name)
        
        # Se não há nova imagem, retorna a existente
        if not image and self.instance and hasattr(self.instance, field_name):
            return getattr(self.instance, field_name)
            
        if image:
            # Verifica a extensão do arquivo
            ext = os.path.splitext(image.name)[1].lower()
            if ext not in allowed_extensions:
                raise ValidationError(f'Formato de arquivo não suportado. Use: {", ".join(allowed_extensions)}')
            
            # Verifica o tamanho do arquivo (máx 5MB)
            max_size = 5 * 1024 * 1024  # 5MB
            if image.size > max_size:
                raise ValidationError(f'O arquivo é muito grande. O tamanho máximo permitido é 5MB.')
            
        return image


class CustomCSSForm(forms.ModelForm):
    class Meta:
        model = CustomCSS
        fields = '__all__'
        widgets = {
            'css': forms.Textarea(attrs={'class': 'font-mono text-xs h-96'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].help_text = 'Identificador único (somente letras, números, hífens e sublinhados)'
        
        # Adiciona classes Tailwind
        for field_name, field in self.fields.items():
            if field_name != 'css':
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                })


class CustomJavaScriptForm(forms.ModelForm):
    class Meta:
        model = CustomJavaScript
        fields = '__all__'
        widgets = {
            'script': forms.Textarea(attrs={'class': 'font-mono text-xs h-96'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['slug'].help_text = 'Identificador único (somente letras, números, hífens e sublinhados)'
        
        # Adiciona classes Tailwind
        for field_name, field in self.fields.items():
            if field_name != 'script':
                field.widget.attrs.update({
                    'class': 'mt-1 block w-full rounded-md border-gray-300 shadow-sm focus:border-blue-500 focus:ring-blue-500 sm:text-sm',
                })


class ThemeExportForm(forms.Form):
    include_css = forms.BooleanField(
        label='Incluir CSS Personalizado',
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'})
    )
    
    include_js = forms.BooleanField(
        label='Incluir JavaScript Personalizado',
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'})
    )
    
    include_media = forms.BooleanField(
        label='Incluir Arquivos de Mídia (logos, favicons, etc.)',
        initial=True,
        widget=forms.CheckboxInput(attrs={'class': 'h-4 w-4 text-blue-600 focus:ring-blue-500 border-gray-300 rounded'})
    )
    
    format_choices = [
        ('zip', 'Arquivo ZIP'),
        ('json', 'Arquivo JSON'),
        ('theme', 'Tema WordPress (se aplicável)'),
    ]
    
    export_format = forms.ChoiceField(
        label='Formato de Exportação',
        choices=format_choices,
        widget=forms.RadioSelect(attrs={'class': 'mt-2'}),
        initial='zip'
    )


class ThemeImportForm(forms.Form):
    theme_file = forms.FileField(
        label='Arquivo do Tema',
        help_text='Selecione um arquivo de tema (.zip, .json, .theme)'
    )
    
    import_type = forms.ChoiceField(
        label='Tipo de Importação',
        choices=[
            ('full', 'Importação Completa (substitui todas as configurações)'),
            ('partial', 'Importação Parcial (mantém configurações existentes)'),
        ],
        widget=forms.RadioSelect(attrs={'class': 'mt-2'}),
        initial='partial'
    )
    
    def clean_theme_file(self):
        theme_file = self.cleaned_data.get('theme_file')
        if theme_file:
            valid_extensions = ['.zip', '.json', '.theme']
            ext = os.path.splitext(theme_file.name)[1].lower()
            if ext not in valid_extensions:
                raise ValidationError('Tipo de arquivo não suportado. Use .zip, .json ou .theme')
            
            # Limita o tamanho do arquivo a 50MB
            max_size = 50 * 1024 * 1024  # 50MB
            if theme_file.size > max_size:
                raise ValidationError(f'O arquivo é muito grande. O tamanho máximo permitido é 50MB')
        
        return theme_file
