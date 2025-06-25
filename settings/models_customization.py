import os
from django.db import models
from django.conf import settings
from django.core.files.storage import FileSystemStorage
from django.core.validators import FileExtensionValidator
from colorfield.fields import ColorField

def logo_upload_path(instance, filename):
    return f'site/logos/{filename}'

def favicon_upload_path(instance, filename):
    return f'site/favicons/{filename}'

class SiteCustomization(models.Model):
    # Identificação
    site_name = models.CharField('Nome do Site', max_length=100, default=settings.SITE_NAME)
    site_slogan = models.CharField('Slogan', max_length=255, blank=True)
    
    # Logos
    logo = models.ImageField(
        'Logo Principal',
        upload_to=logo_upload_path,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'svg'])],
        help_text='Use uma imagem com fundo transparente (recomendado: 250x80px)',
        blank=True
    )
    logo_dark = models.ImageField(
        'Logo para Tema Escuro',
        upload_to=logo_upload_path,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'svg'])],
        help_text='Versão do logo para tema escuro (opcional)',
        blank=True
    )
    logo_footer = models.ImageField(
        'Logo do Rodapé',
        upload_to=logo_upload_path,
        validators=[FileExtensionValidator(['png', 'jpg', 'jpeg', 'svg'])],
        help_text='Versão menor para o rodapé (opcional)',
        blank=True
    )
    favicon = models.ImageField(
        'Favicon',
        upload_to=favicon_upload_path,
        validators=[FileExtensionValidator(['ico', 'png'])],
        help_text='Ícone exibido na aba do navegador (32x32px ou 64x64px)',
        blank=True
    )
    
    # Cores do Tema
    primary_color = ColorField('Cor Primária', default='#4F46E5')
    secondary_color = ColorField('Cor Secundária', default='#10B981')
    success_color = ColorField('Cor de Sucesso', default='#10B981')
    danger_color = ColorField('Cor de Perigo', default='#EF4444')
    warning_color = ColorField('Cor de Aviso', default='#F59E0B')
    info_color = ColorField('Cor de Informação', default='#3B82F6')
    
    # Tipografia
    font_family = models.CharField(
        'Fonte Principal', 
        max_length=255, 
        default="'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, 'Helvetica Neue', Arial, sans-serif"
    )
    font_size_base = models.CharField('Tamanho Base da Fonte', max_length=10, default='1rem')
    
    # Layout
    header_style = models.CharField('Estilo do Cabeçalho', max_length=20, 
                                  choices=[
                                      ('transparent', 'Transparente'),
                                      ('solid', 'Sólido'),
                                      ('glass', 'Vidro Fosco')
                                  ], default='solid')
    footer_style = models.CharField('Estilo do Rodapé', max_length=20, 
                                  choices=[
                                      ('light', 'Claro'),
                                      ('dark', 'Escuro'),
                                      ('primary', 'Cor Primária')
                                  ], default='dark')
    
    # Recursos
    dark_mode = models.BooleanField('Modo Escuro', default=True)
    rtl_support = models.BooleanField('Suporte a RTL', default=False)
    maintenance_mode = models.BooleanField('Modo Manutenção', default=False)
    maintenance_message = models.TextField('Mensagem de Manutenção', blank=True)
    
    # Redes Sociais
    facebook_url = models.URLField('Facebook', blank=True)
    twitter_url = models.URLField('Twitter', blank=True)
    instagram_url = models.URLField('Instagram', blank=True)
    linkedin_url = models.URLField('LinkedIn', blank=True)
    youtube_url = models.URLField('YouTube', blank=True)
    
    # Informações de Contato
    contact_email = models.EmailField('E-mail de Contato', blank=True)
    contact_phone = models.CharField('Telefone de Contato', max_length=20, blank=True)
    contact_address = models.TextField('Endereço', blank=True)
    
    # SEO e Análise
    google_analytics_id = models.CharField('ID do Google Analytics', max_length=50, blank=True)
    google_tag_manager_id = models.CharField('ID do Google Tag Manager', max_length=50, blank=True)
    facebook_pixel_id = models.CharField('ID do Facebook Pixel', max_length=50, blank=True)
    
    # Scripts Personalizados
    header_scripts = models.TextField('Scripts no <head>', blank=True, 
                                    help_text='Código JavaScript que será inserido antes do fechamento da tag </head>')
    footer_scripts = models.TextField('Scripts no final do <body>', blank=True,
                                     help_text='Código JavaScript que será inserido antes do fechamento da tag </body>')
    custom_css = models.TextField('CSS Personalizado', blank=True,
                                 help_text='Estilos CSS personalizados que serão aplicados em todas as páginas')
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Personalização do Site'
        verbose_name_plural = 'Personalizações do Site'

    def __str__(self):
        return f'Personalização - {self.site_name}'
    
    def save(self, *args, **kwargs):
        # Garante que apenas uma instância exista
        if SiteCustomization.objects.exists() and not self.pk:
            # Se já existe uma instância, atualiza em vez de criar nova
            existing = SiteCustomization.objects.first()
            self.id = existing.id
            self.pk = existing.pk
            
        super().save(*args, **kwargs)
        
        # Atualiza as configurações do site em tempo real
        self.update_settings()
    
    def update_settings(self):
        """Atualiza as configurações do site em tempo de execução"""
        from django.conf import settings
        
        # Atualiza o nome do site nas configurações
        if hasattr(settings, 'SITE_NAME'):
            settings.SITE_NAME = self.site_name
            
        # Atualiza as configurações de cores
        if not hasattr(settings, 'THEME'):
            settings.THEME = {}
            
        settings.THEME.update({
            'PRIMARY_COLOR': self.primary_color,
            'SECONDARY_COLOR': self.secondary_color,
            'SUCCESS_COLOR': self.success_color,
            'DANGER_COLOR': self.danger_color,
            'WARNING_COLOR': self.warning_color,
            'INFO_COLOR': self.info_color,
            'FONT_FAMILY': self.font_family,
            'FONT_SIZE_BASE': self.font_size_base,
        })
        
        # Ativa/desativa o modo de manutenção
        settings.MAINTENANCE_MODE = self.maintenance_mode
        
        # Atualiza as configurações de contato
        if not hasattr(settings, 'CONTACT_INFO'):
            settings.CONTACT_INFO = {}
            
        settings.CONTACT_INFO.update({
            'email': self.contact_email,
            'phone': self.contact_phone,
            'address': self.contact_address,
        })
        
        # Atualiza as configurações de mídia social
        if not hasattr(settings, 'SOCIAL_MEDIA'):
            settings.SOCIAL_MEDIA = {}
            
        settings.SOCIAL_MEDIA.update({
            'facebook': self.facebook_url,
            'twitter': self.twitter_url,
            'instagram': self.instagram_url,
            'linkedin': self.linkedin_url,
            'youtube': self.youtube_url,
        })
        
        # Atualiza as configurações de análise
        if not hasattr(settings, 'ANALYTICS'):
            settings.ANALYTICS = {}
            
        settings.ANALYTICS.update({
            'google_analytics': self.google_analytics_id,
            'google_tag_manager': self.google_tag_manager_id,
            'facebook_pixel': self.facebook_pixel_id,
        })


class CustomCSS(models.Model):
    name = models.CharField('Nome do Estilo', max_length=100)
    slug = models.SlugField('Slug', max_length=100, unique=True)
    css = models.TextField('Código CSS')
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'CSS Personalizado'
        verbose_name_plural = 'CSS Personalizados'
        ordering = ['name']
    
    def __str__(self):
        return self.name


class CustomJavaScript(models.Model):
    name = models.CharField('Nome do Script', max_length=100)
    slug = models.SlugField('Slug', max_length=100, unique=True)
    script = models.TextField('Código JavaScript')
    location = models.CharField('Localização', max_length=10, 
                               choices=[
                                   ('head', 'No <head>'),
                                   ('header', 'Após o <header>'),
                                   ('footer', 'Antes de </body>'),
                               ], default='footer')
    is_active = models.BooleanField('Ativo', default=True)
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)
    
    class Meta:
        verbose_name = 'JavaScript Personalizado'
        verbose_name_plural = 'JavaScripts Personalizados'
        ordering = ['name']
    
    def __str__(self):
        return self.name
