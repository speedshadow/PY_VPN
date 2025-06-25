from django.db import models
from django.conf import settings
from django.core.validators import MinValueValidator, MaxValueValidator
import json
import logging
from django.contrib.sites.models import Site
from django.conf import settings as django_settings # Alias to avoid conflict with app name
from urllib.parse import urlparse

logger = logging.getLogger(__name__)

class SiteSettings(models.Model):
    # Configurações Básicas
    site_name = models.CharField('Nome do Site', max_length=100, default='Meu Site')
    site_url = models.URLField('URL do Site', default='http://localhost:8000')
    contact_email = models.EmailField('E-mail de Contato', default='contato@meusite.com')
    favicon = models.ImageField('Favicon', upload_to='site_settings/favicons/', blank=True, null=True, help_text='Ícone exibido na aba do navegador (32x32px ou 64x64px, .ico ou .png)')
    
    # Configurações de SEO
    seo_title = models.CharField('Título SEO', max_length=255, default='Meu Site - Título')
    seo_description = models.TextField('Descrição SEO', default='Descrição do meu site')
    seo_keywords = models.TextField('Palavras-chave', blank=True, help_text='Separadas por vírgula')
    google_analytics_id = models.CharField('ID do Google Analytics', max_length=50, blank=True)
    google_site_verification = models.CharField('Verificação do Google', max_length=255, blank=True)
    
    # Configurações de Manutenção
    maintenance_mode = models.BooleanField('Modo Manutenção', default=False)
    maintenance_message = models.TextField('Mensagem de Manutenção', blank=True)
    
    # Configurações de Segurança
    enable_https = models.BooleanField('Forçar HTTPS', default=False, 
        help_text='Redireciona todo o tráfego para HTTPS')
    enable_hsts = models.BooleanField('HSTS', default=True,
        help_text='HTTP Strict Transport Security')
    hsts_max_age = models.PositiveIntegerField('HSTS Max Age (segundos)', default=31536000,
        validators=[MinValueValidator(0)])
    enable_xss_filter = models.BooleanField('XSS Filter', default=True)
    enable_content_type_nosniff = models.BooleanField('X-Content-Type-Options', default=True)
    enable_x_frame_options = models.BooleanField('X-Frame-Options', default=True)
    x_frame_options = models.CharField('X-Frame-Options', max_length=20, default='DENY',
        choices=[('DENY', 'Negar'), ('SAMEORIGIN', 'Mesma Origem')])
    
    # Configurações de Sessão
    session_cookie_secure = models.BooleanField('Sessão Segura (HTTPS apenas)', default=not settings.DEBUG)
    session_cookie_http_only = models.BooleanField('HTTP Only', default=True)
    session_cookie_samesite = models.CharField('SameSite', max_length=20, default='Lax',
        choices=[('Lax', 'Lax'), ('Strict', 'Strict'), ('None', 'None')])
    csrf_cookie_secure = models.BooleanField('CSRF Seguro (HTTPS apenas)', default=not settings.DEBUG)
    csrf_cookie_http_only = models.BooleanField('CSRF HTTP Only', default=True)
    
    # Configurações de Login Seguro
    enable_2fa = models.BooleanField('Autenticação em Dois Fatores', default=False)
    password_min_length = models.PositiveIntegerField('Tamanho Mínimo de Senha', default=8)
    password_require_uppercase = models.BooleanField('Exigir Letra Maiúscula', default=True)
    password_require_lowercase = models.BooleanField('Exigir Letra Minúscula', default=True)
    password_require_number = models.BooleanField('Exigir Número', default=True)
    password_require_special_char = models.BooleanField('Exigir Caractere Especial', default=True)
    
    # Configurações de Bloqueio de Conta
    axes_failure_limit = models.PositiveIntegerField(
        'Tentativas de Login Antes do Bloqueio', 
        default=5,
        help_text='Número de tentativas de login malsucedidas antes do bloqueio'
    )
    axes_cooloff_time = models.PositiveIntegerField(
        'Tempo de Bloqueio (horas)', 
        default=1,
        help_text='Tempo que o usuário permanece bloqueado após exceder o limite de tentativas'
    )
    axes_lock_out_at_failure = models.BooleanField(
        'Bloquear ao Atingir o Limite', 
        default=True,
        help_text='Bloquear imediatamente ao atingir o número máximo de tentativas'
    )
    axes_use_user_agent = models.BooleanField(
        'Diferenciar por Navegador', 
        default=True,
        help_text='Considerar o user-agent ao bloquear acessos'
    )
    axes_only_user_failure = models.BooleanField(
        'Bloquear Apenas por Usuário', 
        default=False,
        help_text='Se habilitado, bloqueia apenas por nome de usuário, não por IP'
    )
    axes_reset_on_success = models.BooleanField(
        'Reiniciar Contador no Sucesso', 
        default=True,
        help_text='Reiniciar a contagem de tentativas após um login bem-sucedido'
    )
    
    # Configurações Avançadas
    security_headers = models.JSONField(
        'Cabeçalhos de Segurança', 
        default=dict, 
        blank=True,
        help_text='Configurações avançadas de cabeçalhos de segurança'
    )
    
    # Metadados
    created_at = models.DateTimeField('Criado em', auto_now_add=True)
    updated_at = models.DateTimeField('Atualizado em', auto_now=True)

    class Meta:
        verbose_name = 'Configurações do Site'
        verbose_name_plural = 'Configurações do Site'
    
    def __str__(self):
        return self.site_name
    
    def save(self, *args, **kwargs):
        # Garante que apenas uma instância exista
        if SiteSettings.objects.exists() and not self.pk:
            # Se já existe uma instância, atualiza ela em vez de criar uma nova
            existing = SiteSettings.objects.first()
            self.pk = existing.pk
        
        # Aplica as configurações de segurança
        self.apply_security_settings()
        
        super().save(*args, **kwargs)

        # Sync with django.contrib.sites.models.Site for sitemap generation
        if self.pk: # Ensure this instance is saved and has a PK
            try:
                current_site_obj = Site.objects.get(pk=django_settings.SITE_ID)
                
                parsed_url = urlparse(self.site_url)
                new_domain = parsed_url.netloc # Extracts 'domain:port' or 'domain'
                
                needs_site_model_save = False
                if current_site_obj.domain != new_domain:
                    current_site_obj.domain = new_domain
                    needs_site_model_save = True
                    logger.info(f"Updating django.contrib.sites.models.Site (ID: {django_settings.SITE_ID}) domain to: {new_domain}")
                
                if current_site_obj.name != self.site_name:
                    current_site_obj.name = self.site_name
                    needs_site_model_save = True
                    logger.info(f"Updating django.contrib.sites.models.Site (ID: {django_settings.SITE_ID}) name to: {self.site_name}")

                if needs_site_model_save:
                    current_site_obj.save()

            except Site.DoesNotExist:
                logger.error(f"Site with ID {django_settings.SITE_ID} not found in django.contrib.sites.models.Site. Cannot sync sitemap domain/name.")
            except Exception as e:
                logger.error(f"Error syncing SiteSettings with django.contrib.sites.models.Site: {e}")
    
    def apply_security_settings(self):
        """Aplica as configurações de segurança ao settings do Django"""
        from django.conf import settings
        
        # Configurações de HTTPS
        if hasattr(settings, 'SECURE_SSL_REDIRECT'):
            settings.SECURE_SSL_REDIRECT = self.enable_https
        
        # Configurações de Sessão
        settings.SESSION_COOKIE_SECURE = self.session_cookie_secure
        settings.SESSION_COOKIE_HTTPONLY = self.session_cookie_http_only
        settings.SESSION_COOKIE_SAMESITE = self.session_cookie_samesite
        
        # Configurações CSRF
        settings.CSRF_COOKIE_SECURE = self.csrf_cookie_secure
        settings.CSRF_COOKIE_HTTPONLY = self.csrf_cookie_http_only
        
        # Outros cabeçalhos de segurança
        settings.SECURE_BROWSER_XSS_FILTER = self.enable_xss_filter
        settings.SECURE_CONTENT_TYPE_NOSNIFF = self.enable_content_type_nosniff
        settings.X_FRAME_OPTIONS = self.x_frame_options
        
        # HSTS
        if self.enable_hsts and self.enable_https:
            settings.SECURE_HSTS_SECONDS = self.hsts_max_age
            settings.SECURE_HSTS_INCLUDE_SUBDOMAINS = True
            settings.SECURE_HSTS_PRELOAD = True
        
        # Configurações de senha
        settings.AUTH_PASSWORD_VALIDATORS = [
            {
                'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
            },
            {
                'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
                'OPTIONS': {
                    'min_length': self.password_min_length,
                }
            },
            {
                'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
            },
            {
                'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
            },
        ]
        
        # Aplica configurações personalizadas de segurança
        for key, value in self.security_headers.items():
            setattr(settings, key, value)
    
    @classmethod
    def get_solo(cls):
        """Retorna a única instância de configurações ou cria uma nova"""
        obj, created = cls.objects.get_or_create(pk=1)
        return obj
    
    def toggle_maintenance(self, status: bool):
        """Ativa/desativa o modo de manutenção"""
        self.maintenance_mode = status
        self.save()
        logger.info(f"Modo de manutenção {'ativado' if status else 'desativado'}")
    
    def update_security_settings(self, **kwargs):
        """Atualiza as configurações de segurança"""
        for key, value in kwargs.items():
            if hasattr(self, key):
                setattr(self, key, value)
        self.save()
        logger.info("Configurações de segurança atualizadas")
    
    def get_security_status(self):
        """Retorna o status atual das configurações de segurança"""
        return {
            'https_enabled': self.enable_https,
            'hsts_enabled': self.enable_hsts and self.enable_https,
            'xss_protection': self.enable_xss_filter,
            'content_type_nosniff': self.enable_content_type_nosniff,
            'x_frame_options': self.enable_x_frame_options,
            'secure_cookies': self.session_cookie_secure and self.csrf_cookie_secure,
            'http_only_cookies': self.session_cookie_http_only and self.csrf_cookie_http_only,
            'axes_enabled': self.axes_failure_limit > 0,
        }
