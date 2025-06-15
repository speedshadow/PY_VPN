from settings.models import SiteSettings
from categories.models import Category

def settings_context(request):
    settings = SiteSettings.objects.first()
    if not settings:
        # fallback para evitar erro em ambiente de teste
        from types import SimpleNamespace
        settings = SimpleNamespace(site_name='VPN Review Site', seo_title='VPN Review Site', seo_description='Best VPN reviews, comparisons and coupons.')
    navbar_categories = Category.objects.all().order_by('name')
    return {'settings': settings, 'navbar_categories': navbar_categories}
