from django import forms
from django.core.exceptions import ValidationError
from django.utils.safestring import mark_safe
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
from .models_seo import SEOSettings, PageSEO, XMLSitemap

class SEOSettingsForm(forms.ModelForm):
    class Meta:
        model = SEOSettings
        fields = '__all__'
        widgets = {
            'meta_keywords': forms.Textarea(attrs={'rows': 3, 'placeholder': 'palavra1, palavra2, palavra3'}),
            'meta_description': forms.Textarea(attrs={'rows': 3, 'maxlength': '160'}),
            'og_description': forms.Textarea(attrs={'rows': 3, 'maxlength': '300'}),
            'structured_data': forms.Textarea(attrs={'rows': 10, 'class': 'font-mono text-xs'}),
            'sitemap_priority': forms.NumberInput(attrs={
                'min': '0.0',
                'max': '1.0',
                'step': '0.1'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['meta_description'].help_text = 'Recomendado: 150-160 caracteres. Atual: <span id="meta_desc_count">0</span>'
        self.fields['og_description'].help_text = 'Recomendado: até 300 caracteres. Atual: <span id="og_desc_count">0</span>'
    
    def clean_meta_description(self):
        meta_desc = self.cleaned_data.get('meta_description', '')
        if len(meta_desc) > 160:
            self.add_warning('meta_description', 'Descrição muito longa para resultados de busca (máx. 160 caracteres).')
        return meta_desc
    
    def clean_og_description(self):
        og_desc = self.cleaned_data.get('og_description', '')
        if len(og_desc) > 300:
            self.add_warning('og_description', 'Descrição muito longa para redes sociais (máx. 300 caracteres).')
        return og_desc
    
    def clean_structured_data(self):
        import json
        data = self.cleaned_data.get('structured_data', '').strip()
        if data:
            try:
                json.loads(data)
            except json.JSONDecodeError as e:
                raise ValidationError(f'JSON inválido: {str(e)}')
        return data


class PageSEOForm(forms.ModelForm):
    class Meta:
        model = PageSEO
        fields = '__all__'
        widgets = {
            'meta_keywords': forms.Textarea(attrs={'rows': 2, 'placeholder': 'palavra1, palavra2, palavra3'}),
            'meta_description': forms.Textarea(attrs={'rows': 3, 'maxlength': '160'}),
            'og_description': forms.Textarea(attrs={'rows': 3, 'maxlength': '300'}),
            'structured_data': forms.Textarea(attrs={'rows': 10, 'class': 'font-mono text-xs'}),
            'sitemap_priority': forms.NumberInput(attrs={
                'min': '0.0',
                'max': '1.0',
                'step': '0.1'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['meta_description'].help_text = 'Recomendado: 150-160 caracteres. Atual: <span id="meta_desc_count">0</span>'
        self.fields['og_description'].help_text = 'Recomendado: até 300 caracteres. Atual: <span id="og_desc_count">0</span>'
        
        # Torna o campo page_type somente leitura na edição
        if self.instance and self.instance.pk:
            self.fields['page_type'].disabled = True
    
    def clean_structured_data(self):
        import json
        data = self.cleaned_data.get('structured_data', '').strip()
        if data:
            try:
                json.loads(data)
            except json.JSONDecodeError as e:
                raise ValidationError(f'JSON inválido: {str(e)}')
        return data


class XMLSitemapForm(forms.ModelForm):
    class Meta:
        model = XMLSitemap
        exclude = ['created_at', 'updated_at', 'lastmod']
        widgets = {
            'url': forms.TextInput(attrs={'placeholder': '/caminho/para/pagina'}), # Alterado para TextInput e placeholder
            'priority': forms.NumberInput(attrs={
                'min': '0.0',
                'max': '1.0',
                'step': '0.1'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['url'].help_text = "Insira o caminho relativo (ex: /sobre-nos) ou uma URL completa se for um domínio externo." # Adicionar help_text

    def clean_url(self):
        url = self.cleaned_data.get('url', '').strip()
        if not url:
            raise ValidationError('Este campo é obrigatório.') # Garantir que não está vazio
        
        # Permitir caminhos relativos começando com / OU URLs completas
        if url.startswith('/') or url.startswith(('http://', 'https://')):
            if url.startswith('/') and not url.startswith('//') and len(url) > 1 and ' ' in url.strip():
                 raise ValidationError('O caminho relativo não deve conter espaços.')
            # Poderia adicionar mais validações para caminhos relativos aqui se necessário (ex: caracteres inválidos)
            return url
        else:
            raise ValidationError('A URL deve ser um caminho relativo (ex: /caminho/pagina) ou uma URL completa (http://... ou https://...).')


class SitemapGenerationForm(forms.Form):
    INCLUDE_CHOICES = [
        ('pages', 'Páginas do Site'),
        ('blog', 'Posts do Blog'),
        ('products', 'Produtos'),
        ('categories', 'Categorias'),
        ('tags', 'Tags'),
        ('custom', 'URLs Personalizadas'),
    ]
    
    include = forms.MultipleChoiceField(
        label='Incluir no Sitemap',
        choices=INCLUDE_CHOICES,
        widget=forms.CheckboxSelectMultiple,
        initial=['pages', 'blog', 'products']
    )
    
    priority = forms.FloatField(
        label='Prioridade Padrão',
        initial=0.5,
        min_value=0.0,
        max_value=1.0,
        step_size=0.1,
        help_text='Prioridade das URLs (0.0 a 1.0)'
    )
    
    changefreq = forms.ChoiceField(
        label='Frequência de Mudança Padrão',
        choices=PageSEO._meta.get_field('sitemap_changefreq').choices,
        initial='weekly',
        help_text='Com que frequência a página é alterada?'
    )
    
    lastmod = forms.ChoiceField(
        label='Data da Última Modificação',
        choices=[
            ('now', 'Data/Hora Atual'),
            ('modified', 'Data de Modificação do Conteúdo'),
            ('none', 'Não Incluir')
        ],
        initial='now',
        help_text='Como definir a data da última modificação?'
    )
    
    limit = forms.IntegerField(
        label='Limite de URLs',
        min_value=1,
        max_value=50000,
        initial=1000,
        required=False,
        help_text='Número máximo de URLs a serem incluídas (deixe em branco para ilimitado)'
    )
    
    def clean_limit(self):
        limit = self.cleaned_data.get('limit')
        if not limit:
            return None
        return limit
