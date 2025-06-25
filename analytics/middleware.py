import re
import user_agents
from .models import Analytics

def get_client_ip(request):
    """
    Obtém o endereço IP real do cliente, mesmo quando por trás de um proxy.
    """
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # O cabeçalho pode conter múltiplos IPs (ex: "client, proxy1, proxy2")
        # O primeiro é o IP do cliente original.
        ip = x_forwarded_for.split(',')[0].strip()
    else:
        # Se não houver proxy, use o endereço remoto padrão.
        ip = request.META.get('REMOTE_ADDR')
    return ip
from django.utils import timezone
from analytics.models import Analytics

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
        # Log a visita apenas para respostas bem-sucedidas (código 2xx)
        # e para páginas HTML, para evitar logging de assets, APIs, etc.
        if 200 <= response.status_code < 300 and 'text/html' in response.get('Content-Type', ''):
            self.log_visit(request)
        return response

    def log_visit(self, request):
        # Ignorar caminhos de admin, dashboard e ficheiros estáticos/media
        path = request.path
        if path.startswith(('/admin', '/dashboard', '/static', '/media')):
            return

        user_agent_string = request.META.get('HTTP_USER_AGENT', '')
        
        # Evitar user agents excessivamente longos que podem quebrar a base de dados
        if len(user_agent_string) > 512:
            user_agent_string = user_agent_string[:512]

        try:
            ua = user_agents.parse(user_agent_string)
            is_bot = ua.is_bot
        except Exception:
            ua = None
            is_bot = False

        # Detetar bots de forma mais fiável
        if not is_bot:
            is_bot = bool(re.search(r'(bot|crawl|spider|slurp|bingpreview)', user_agent_string, re.I))
        
        ip_address = get_client_ip(request)

        # Não registar se não conseguirmos obter um IP
        if not ip_address:
            return

        Analytics.objects.create(
            ip_address=ip_address,
            user_agent=user_agent_string
        )
        self.log_visit(request)
        return response

    def log_visit(self, request):
        # Ignore admin and static/media
        path = request.path
        if path.startswith('/admin') or path.startswith('/dashboard') or path.startswith('/static') or path.startswith('/media'):
            return
        user_agent = request.META.get('HTTP_USER_AGENT', '')
        ua = user_agents.parse(user_agent)
        is_bot = bool(re.search(r'(bot|crawl|spider|slurp|bingpreview)', user_agent, re.I))
        Analytics.objects.create(
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=user_agent,
            is_bot=is_bot,
            page_url=path,
            referrer=request.META.get('HTTP_REFERER', ''),
            event_type='bot' if is_bot else 'visit'
        )
