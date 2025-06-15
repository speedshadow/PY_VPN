import re
import user_agents
from django.utils import timezone
from analytics.models import Analytics

class AnalyticsMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        response = self.get_response(request)
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
            event_type='bot' if is_bot else 'visit',
        )
