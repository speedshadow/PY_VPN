import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.db import transaction
from django.urls import reverse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils.text import slugify
from django.contrib.sitemaps import Sitemap
from django.contrib.sites.models import Site
from .models_seo import SEOSettings, PageSEO, XMLSitemap
from .forms_seo import SEOSettingsForm, PageSEOForm, XMLSitemapForm, SitemapGenerationForm

logger = logging.getLogger(__name__)

# Helpers

def get_sitemap_urls(request):
    """Gera a lista de URLs para o sitemap"""
    current_site = Site.objects.get_current()
    base_url = f"https://{current_site.domain}"
    
    # URLs padrão do site
    urls = [
        {'location': base_url, 'priority': '1.0', 'changefreq': 'daily'},
        {'location': f"{base_url}/sobre/", 'priority': '0.8', 'changefreq': 'weekly'},
        {'location': f"{base_url}/contato/", 'priority': '0.8', 'changefreq': 'weekly'},
    ]
    
    # Adiciona URLs do sitemap personalizado
    for item in XMLSitemap.objects.filter(is_active=True):
        urls.append({
            'location': item.url,
            'lastmod': item.lastmod or timezone.now(),
            'changefreq': item.changefreq,
            'priority': str(item.priority),
        })
    
    return urls

# Views

@login_required
@permission_required('settings.view_seosettings')
def seo_dashboard(request):
    """Painel de controle de SEO"""
    seo_settings = SEOSettings.objects.first()
    page_seo = PageSEO.objects.all()
    sitemap_urls = get_sitemap_urls(request)
    
    # Análise básica de SEO
    seo_score = 0
    issues = []
    
    if seo_settings:
        # Verifica meta descrição
        if not seo_settings.meta_description:
            issues.append('Adicione uma meta descrição')
        elif len(seo_settings.meta_description) < 120:
            issues.append('Meta descrição muito curta (mínimo 120 caracteres)')
        elif len(seo_settings.meta_description) > 160:
            issues.append('Meta descrição muito longa (máximo 160 caracteres)')
        else:
            seo_score += 25
        
        # Verifica palavras-chave
        if not seo_settings.meta_keywords:
            issues.append('Adicione palavras-chave')
        else:
            seo_score += 15
        
        # Verifica configurações de redes sociais
        if not seo_settings.og_title or not seo_settings.og_description:
            issues.append('Configure os metadados para redes sociais (Open Graph)')
        else:
            seo_score += 20
            
        # Verifica dados estruturados
        if not seo_settings.structured_data:
            issues.append('Adicione dados estruturados (schema.org)')
        else:
            seo_score += 15
            
        # Verifica configurações básicas
        if seo_settings.meta_robots:
            seo_score += 15
        else:
            issues.append('Configure as diretivas para robôs de busca')
            
        if seo_settings.canonical_url:
            seo_score += 10
        else:
            issues.append('Configure a URL canônica')
    else:
        issues.append('Configure as configurações de SEO do site')
    
    context = {
        'seo_settings': seo_settings,
        'page_seo_count': page_seo.count(),
        'sitemap_urls': sitemap_urls[:5],  # Mostra apenas as 5 primeiras URLs
        'sitemap_total': len(sitemap_urls),
        'seo_score': min(100, seo_score),  # Garante que não ultrapasse 100%
        'issues': issues,
        'title': 'Dashboard de SEO'
    }
    
    return render(request, 'dashboard/seo/dashboard.html', context)

@login_required
@permission_required('settings.change_seosettings')
def seo_settings_edit(request):
    """Edita as configurações gerais de SEO"""
    seo_settings = SEOSettings.objects.first()
    
    if request.method == 'POST':
        form = SEOSettingsForm(request.POST, request.FILES, instance=seo_settings)
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações de SEO atualizadas com sucesso!')
            return redirect('seo_dashboard')
    else:
        form = SEOSettingsForm(instance=seo_settings)
    
    return render(request, 'dashboard/seo/settings_form.html', {
        'form': form,
        'title': 'Configurações Gerais de SEO'
    })

@login_required
@permission_required('settings.view_pageseo')
def page_seo_list(request):
    """Lista todas as configurações de SEO por página"""
    page_seo_list = PageSEO.objects.all().order_by('page_type')
    
    # Paginação
    paginator = Paginator(page_seo_list, 10)  # 10 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/seo/page_seo_list.html', {
        'page_obj': page_obj,
        'title': 'SEO por Página'
    })

@login_required
@permission_required('settings.change_pageseo')
def page_seo_edit(request, pk=None):
    """Edita ou cria uma configuração de SEO para uma página"""
    if pk:
        page_seo = get_object_or_404(PageSEO, pk=pk)
        title = f'Editar SEO - {page_seo.get_page_type_display()}'
    else:
        page_seo = None
        title = 'Adicionar Configuração de Página'
    
    if request.method == 'POST':
        form = PageSEOForm(request.POST, instance=page_seo)
        if form.is_valid():
            page_seo = form.save()
            messages.success(request, 'Configuração de página salva com sucesso!')
            return redirect('page_seo_list')
    else:
        form = PageSEOForm(instance=page_seo)
    
    return render(request, 'dashboard/seo/page_seo_form.html', {
        'form': form,
        'page_seo': page_seo,
        'title': title
    })

@login_required
@permission_required('settings.delete_pageseo')
def page_seo_delete(request, pk):
    """Remove uma configuração de SEO de página"""
    page_seo = get_object_or_404(PageSEO, pk=pk)
    
    if request.method == 'POST':
        page_seo.delete()
        messages.success(request, 'Configuração de página removida com sucesso!')
        return redirect('page_seo_list')
    
    return render(request, 'dashboard/seo/confirm_delete.html', {
        'object': page_seo,
        'title': 'Confirmar Exclusão de Configuração de Página'
    })

@login_required
@permission_required('settings.view_xmlsitemap')
def sitemap_list(request):
    """Lista todas as URLs do sitemap"""
    sitemap_urls = XMLSitemap.objects.all().order_by('-priority', 'url')
    
    # Paginação
    paginator = Paginator(sitemap_urls, 20)  # 20 itens por página
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/seo/sitemap_list.html', {
        'page_obj': page_obj,
        'title': 'URLs do Sitemap'
    })

@login_required
@permission_required('settings.add_xmlsitemap')
def sitemap_add(request):
    """Adiciona uma nova URL ao sitemap"""
    if request.method == 'POST':
        form = XMLSitemapForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, 'URL adicionada ao sitemap com sucesso!')
            return redirect('sitemap_list')
    else:
        form = XMLSitemapForm()
    
    return render(request, 'dashboard/seo/sitemap_form.html', {
        'form': form,
        'title': 'Adicionar URL ao Sitemap'
    })

@login_required
@permission_required('settings.change_xmlsitemap')
def sitemap_edit(request, pk):
    """Edita uma URL do sitemap"""
    sitemap_url = get_object_or_404(XMLSitemap, pk=pk)
    
    if request.method == 'POST':
        form = XMLSitemapForm(request.POST, instance=sitemap_url)
        if form.is_valid():
            form.save()
            messages.success(request, 'URL do sitemap atualizada com sucesso!')
            return redirect('sitemap_list')
    else:
        form = XMLSitemapForm(instance=sitemap_url)
    
    return render(request, 'dashboard/seo/sitemap_form.html', {
        'form': form,
        'title': 'Editar URL do Sitemap',
        'sitemap_url': sitemap_url
    })

@login_required
@permission_required('settings.delete_xmlsitemap')
def sitemap_delete(request, pk):
    """Remove uma URL do sitemap"""
    sitemap_url = get_object_or_404(XMLSitemap, pk=pk)
    
    if request.method == 'POST':
        sitemap_url.delete()
        messages.success(request, 'URL removida do sitemap com sucesso!')
        return redirect('sitemap_list')
    
    return render(request, 'dashboard/seo/confirm_delete.html', {
        'object': sitemap_url,
        'title': 'Confirmar Exclusão de URL do Sitemap'
    })

@login_required
@permission_required('settings.view_xmlsitemap')
def sitemap_generate(request):
    """Gera o sitemap.xml dinamicamente"""
    if request.method == 'POST':
        form = SitemapGenerationForm(request.POST)
        if form.is_valid():
            # Aqui você pode adicionar lógica para gerar o sitemap
            # com base nas opções selecionadas
            messages.success(request, 'Sitemap gerado com sucesso!')
            return redirect('sitemap_list')
    else:
        form = SitemapGenerationForm()
    
    return render(request, 'dashboard/seo/sitemap_generate.html', {
        'form': form,
        'title': 'Gerar Sitemap XML'
    })

@login_required
@permission_required('settings.view_xmlsitemap')
def sitemap_download(request):
    """Faz o download do sitemap.xml"""
    urls = get_sitemap_urls(request)
    
    # Renderiza o template do sitemap
    xml_content = render_to_string('seo/sitemap.xml', {
        'urls': urls,
        'site': Site.objects.get_current(),
    })
    
    # Cria a resposta com o conteúdo XML
    response = HttpResponse(xml_content, content_type='application/xml')
    response['Content-Disposition'] = 'attachment; filename="sitemap.xml"'
    return response

@login_required
@permission_required('settings.view_seosettings')
def seo_analysis(request):
    """Faz uma análise detalhada do SEO do site"""
    # Esta é uma implementação básica - você pode expandir com mais verificações
    seo_settings = SEOSettings.objects.first()
    
    analysis = {
        'meta': {
            'title': 'Meta Tags',
            'status': 'warning',
            'items': [],
            'score': 0,
            'max_score': 5
        },
        'content': {
            'title': 'Conteúdo',
            'status': 'warning',
            'items': [],
            'score': 0,
            'max_score': 5
        },
        'performance': {
            'title': 'Desempenho',
            'status': 'warning',
            'items': [],
            'score': 0,
            'max_score': 5
        },
        'mobile': {
            'title': 'Mobile',
            'status': 'warning',
            'items': [],
            'score': 0,
            'max_score': 5
        },
        'security': {
            'title': 'Segurança',
            'status': 'warning',
            'items': [],
            'score': 0,
            'max_score': 5
        },
    }
    
    # Verificações de Meta Tags
    if seo_settings and seo_settings.meta_title:
        analysis['meta']['score'] += 1
        analysis['meta']['items'].append({
            'status': 'success',
            'text': 'Título da página configurado',
            'details': seo_settings.meta_title
        })
    else:
        analysis['meta']['items'].append({
            'status': 'error',
            'text': 'Adicione um título à página',
            'details': 'O título da página é essencial para SEO'
        })
    
    # Adicione mais verificações aqui...
    
    # Calcula a pontuação total
    total_score = sum(cat['score'] for cat in analysis.values())
    max_total = sum(cat['max_score'] for cat in analysis.values())
    
    # Atualiza o status com base na pontuação
    for category in analysis.values():
        percentage = (category['score'] / category['max_score']) * 100
        if percentage >= 80:
            category['status'] = 'success'
        elif percentage >= 50:
            category['status'] = 'warning'
        else:
            category['status'] = 'error'
    
    return render(request, 'dashboard/seo/analysis.html', {
        'analysis': analysis,
        'total_score': total_score,
        'max_total': max_total,
        'score_percentage': int((total_score / max_total) * 100) if max_total > 0 else 0,
        'title': 'Análise de SEO'
    })

# Views Públicas

def robots_txt(request):
    """Gera o arquivo robots.txt dinamicamente"""
    seo_settings = SEOSettings.objects.first()
    
    # Conteúdo padrão do robots.txt
    lines = [
        'User-agent: *',
    ]
    
    # Adiciona diretivas de robots personalizadas
    if seo_settings and seo_settings.meta_robots:
        robots_directives = seo_settings.meta_robots.split(',')
        if 'noindex' in robots_directives:
            lines.append('Disallow: /')
        else:
            lines.append('Allow: /')
            
            # Adiciona sitemap
            lines.append(f'Sitemap: {request.build_absolute_uri(reverse("sitemap_xml"))}')
    else:
        lines.append('Allow: /')
    
    # Adiciona regras personalizadas do sitemap
    for url in XMLSitemap.objects.filter(is_active=True):
        if url.meta_robots and 'noindex' in url.meta_robots:
            lines.append(f'Disallow: {url.url}')
    
    # Junta as linhas e retorna a resposta
    content = '\n'.join(lines) + '\n'
    return HttpResponse(content, content_type='text/plain')


def sitemap_xml(request):
    """Gera o sitemap.xml dinamicamente"""
    urls = get_sitemap_urls(request)
    
    # Renderiza o template do sitemap
    xml_content = render_to_string('seo/sitemap.xml', {
        'urls': urls,
        'site': Site.objects.get_current(),
    })
    
    return HttpResponse(xml_content, content_type='application/xml')

# API Views

@csrf_exempt
@require_http_methods(["POST"])
def api_track_seo(request):
    """API para rastreamento de métricas de SEO"""
    try:
        data = json.loads(request.body)
        # Aqui você pode processar e salvar os dados de rastreamento
        # Exemplo: cliques, impressões, taxas de rejeição, etc.
        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao rastrear métricas de SEO: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

# Sitemap para o Django Sitemap Framework

class CustomSitemap(Sitemap):
    changefreq = "weekly"
    priority = 0.5
    protocol = 'https'
    
    def items(self):
        # Retorna todas as URLs do sitemap personalizado
        return XMLSitemap.objects.filter(is_active=True)
    
    def location(self, item):
        return item.url
    
    def lastmod(self, item):
        return item.lastmod or None
    
    def changefreq(self, item):
        return item.changefreq or self.changefreq
    
    def priority(self, item):
        return item.priority or self.priority
