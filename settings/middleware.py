from django.conf import settings
from django.core.exceptions import MiddlewareNotUsed
from django.utils.deprecation import MiddlewareMixin
import logging

logger = logging.getLogger(__name__)

class SecurityHeadersMiddleware(MiddlewareMixin):
    """
    Middleware para aplicar cabeçalhos de segurança HTTP baseados nas configurações do site.
    """
    def __init__(self, get_response=None):
        self.get_response = get_response
        # Verifica se o middleware está desativado nas configurações
        if not getattr(settings, 'ENABLE_SECURITY_HEADERS', True):
            logger.warning("SecurityHeadersMiddleware está desativado (ENABLE_SECURITY_HEADERS=False)")
            raise MiddlewareNotUsed("SecurityHeadersMiddleware está desativado")
        
        # Configurações padrão que podem ser sobrescritas
        self.security_headers = {
            'X-Content-Type-Options': 'nosniff',
            'X-Frame-Options': 'DENY',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'same-origin',
            'Permissions-Policy': 'camera=(), microphone=(), geolocation=()',
            'Cross-Origin-Opener-Policy': 'same-origin',
            'Cross-Origin-Resource-Policy': 'same-site',
        }
        
        # Atualiza com as configurações do settings.py, se existirem
        self.security_headers.update(getattr(settings, 'SECURITY_HEADERS', {}))
        
        # Configura o CSP se estiver habilitado
        if getattr(settings, 'CSP_ENABLED', False):
            self._setup_csp()
    
    def _setup_csp(self):
        """Configura a Política de Segurança de Conteúdo (CSP)"""
        from django.conf import settings
        
        csp = {
            'default-src': ["'self'"],
            'script-src': ["'self'", "'unsafe-inline'", "'unsafe-eval'"],
            'style-src': ["'self'", "'unsafe-inline'"],
            'img-src': ["'self'", "data:", "https:"],
            'font-src': ["'self'", "data:"],
            'connect-src': ["'self'"],
            'frame-src': ["'self'"],
            'object-src': ["'none'"],
            'base-uri': ["'self'"],
            'form-action': ["'self'"],
            'frame-ancestors': ["'self'"],
            'upgrade-insecure-requests': [],
        }
        
        # Atualiza com as configurações personalizadas
        csp.update(getattr(settings, 'CSP_HEADERS', {}))
        
        # Formata os cabeçalhos CSP
        csp_parts = []
        for key, values in csp.items():
            if values:
                if isinstance(values, (list, tuple)):
                    csp_parts.append(f"{key} {' '.join(values)}")
                else:
                    csp_parts.append(f"{key} {values}")
        
        self.security_headers['Content-Security-Policy'] = "; ".join(csp_parts)
    
    def process_response(self, request, response):
        """
        Adiciona os cabeçalhos de segurança à resposta HTTP.
        """
        # Não adiciona cabeçalhos para respostas de streaming
        if response.streaming:
            return response
            
        # Não adiciona cabeçalhos para respostas de API (se estiver usando DRF)
        content_type = response.get('Content-Type', '')
        if 'application/json' in content_type or 'api' in request.path:
            return response
        
        # Aplica os cabeçalhos de segurança
        for header, value in self.security_headers.items():
            if header not in response:
                response[header] = value
        
        # Configura o HSTS se estiver habilitado
        if getattr(settings, 'SECURE_HSTS_SECONDS', 0) > 0 and 'Strict-Transport-Security' not in response:
            hsts_max_age = settings.SECURE_HSTS_SECONDS
            hsts_include_subdomains = getattr(settings, 'SECURE_HSTS_INCLUDE_SUBDOMAINS', False)
            hsts_preload = getattr(settings, 'SECURE_HSTS_PRELOAD', False)
            
            hsts_value = f'max-age={hsts_max_age}'
            if hsts_include_subdomains:
                hsts_value += '; includeSubDomains'
            if hsts_preload:
                hsts_value += '; preload'
                
            response['Strict-Transport-Security'] = hsts_value
        
        # Configura os cookies seguros
        if hasattr(response, 'cookies') and getattr(settings, 'SESSION_COOKIE_SECURE', False):
            for cookie in response.cookies.values():
                if 'secure' not in cookie:
                    cookie['secure'] = True
                if 'httponly' not in cookie and cookie.key != 'csrftoken':
                    cookie['httponly'] = True
                if 'samesite' not in cookie and hasattr(settings, 'SESSION_COOKIE_SAMESITE'):
                    cookie['samesite'] = settings.SESSION_COOKIE_SAMESITE
        
        return response


class SiteSettingsMiddleware(MiddlewareMixin):
    """
    Middleware para carregar as configurações do site em todas as requisições.
    """
    def __init__(self, get_response=None):
        self.get_response = get_response
        self.settings = None
        
        # Tenta carregar as configurações do banco de dados
        self._load_settings()
    
    def _load_settings(self):
        """Carrega as configurações do banco de dados"""
        from .models import SiteSettings
        
        try:
            self.settings = SiteSettings.get_solo()
            # Aplica as configurações de segurança
            self.settings.apply_security_settings()
        except Exception as e:
            logger.error(f"Erro ao carregar as configurações do site: {e}")
            # Usa configurações padrão se não conseguir carregar do banco
            self.settings = None
    
    def process_request(self, request):
        """Adiciona as configurações ao objeto de requisição"""
        if self.settings is None:
            self._load_settings()
        
        request.site_settings = self.settings
        return None
    
    def process_response(self, request, response):
        """Adiciona cabeçalhos de segurança adicionais"""
        if hasattr(request, 'site_settings') and request.site_settings:
            settings = request.site_settings
            
            # Adiciona cabeçalho X-Content-Type-Options
            if settings.enable_content_type_nosniff:
                response['X-Content-Type-Options'] = 'nosniff'
            
            # Adiciona cabeçalho X-Frame-Options
            if settings.enable_x_frame_options:
                response['X-Frame-Options'] = settings.x_frame_options
            
            # Adiciona cabeçalho X-XSS-Protection
            if settings.enable_xss_filter:
                response['X-XSS-Protection'] = '1; mode=block'
            
            # Adiciona cabeçalho Referrer-Policy
            response['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Configura cookies seguros
            if settings.session_cookie_secure:
                if hasattr(response, 'cookies'):
                    for cookie in response.cookies.values():
                        if 'secure' not in cookie:
                            cookie['secure'] = True
                        if 'httponly' not in cookie and cookie.key != 'csrftoken':
                            cookie['httponly'] = True
                        if 'samesite' not in cookie and settings.session_cookie_samesite:
                            cookie['samesite'] = settings.session_cookie_samesite
        
        return response
