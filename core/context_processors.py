from settings.models import SiteSettings
from settings.models_compliance import ComplianceSettings # Adicionar esta importação
from categories.models import Category
from types import SimpleNamespace # Mover importação para o topo

def settings_context(request):
    site_settings = SiteSettings.objects.first()
    if not site_settings:
        # fallback para evitar erro em ambiente de teste
        site_settings = SimpleNamespace(
            site_name='VPN Review Site', 
            seo_title='VPN Review Site', 
            seo_description='Best VPN reviews, comparisons and coupons.'
        )

    compliance_settings = ComplianceSettings.objects.first()
    if not compliance_settings:
        # Fallback para compliance_settings se não existir
        # Defina os padrões que fazem sentido para o seu caso se não houver configurações
        compliance_settings = SimpleNamespace(
            cookie_consent_enabled=False, 
            cookie_consent_message='Este site usa cookies para melhorar a sua experiência.',
            # Adicione outros campos de ComplianceSettings com valores padrão se necessário
        )

    navbar_categories = Category.objects.all().order_by('name')
    
    return {
        'settings': site_settings, 
        'compliance_settings': compliance_settings, # Adicionar ao contexto
        'navbar_categories': navbar_categories
    }
