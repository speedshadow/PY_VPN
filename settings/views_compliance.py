import json
import logging
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.http import JsonResponse, HttpResponse, HttpResponseRedirect
from django.conf import settings
from django.views.decorators.http import require_http_methods
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.urls import reverse
from django.core.paginator import Paginator
from django.template.loader import render_to_string
from django.utils.translation import gettext_lazy as _
from django.views.decorators.clickjacking import xframe_options_exempt
from .models_compliance import ComplianceSettings, DataRequest
from .forms_compliance import ComplianceSettingsForm, DataRequestForm, DataRequestResponseForm, CookieConsentForm

logger = logging.getLogger(__name__)

# Helpers

def get_cookie_policy_url():
    """Retorna a URL da política de cookies"""
    try:
        from django.urls import reverse
        return reverse('cookie_policy')
    except:
        return '/politica-de-cookies/'

def get_privacy_policy_url():
    """Retorna a URL da política de privacidade"""
    try:
        from django.urls import reverse
        return reverse('privacy_policy')
    except:
        return '/politica-de-privacidade/'

def get_terms_url():
    """Retorna a URL dos termos de serviço"""
    try:
        from django.urls import reverse
        return reverse('terms_of_service')
    except:
        return '/termos-de-servico/'

# Views

@login_required
@permission_required('settings.view_compliancesettings')
def compliance_dashboard(request):
    """Painel de controle de conformidade"""
    compliance_settings = ComplianceSettings.objects.first()
    
    # Estatísticas
    stats = {
        'data_requests': {
            'total': DataRequest.objects.count(),
            'pending': DataRequest.objects.filter(status='pending').count(),
            'completed': DataRequest.objects.filter(status='completed').count(),
        },
        'cookies': {
            'necessary': True,  # Sempre necessário
            'preferences': compliance_settings.cookie_preferences if compliance_settings else False,
            'analytics': compliance_settings.cookie_analytics if compliance_settings else False,
            'marketing': compliance_settings.cookie_marketing if compliance_settings else False,
        },
        'policies': {
            'privacy_policy': bool(compliance_settings.privacy_policy) if compliance_settings else False,
            'terms_of_service': bool(compliance_settings.terms_of_service) if compliance_settings else False,
            'cookie_policy': bool(compliance_settings.cookie_policy) if compliance_settings else False,
        },
        'compliance': {
            'gdpr': compliance_settings.is_gdpr_compliant if compliance_settings else False,
            'ccpa': compliance_settings.is_ccpa_compliant if compliance_settings else False,
            'age_restriction': compliance_settings.age_restriction if compliance_settings else 13,
        },
    }
    
    # Verificações de conformidade
    compliance_checks = {
        'gdpr': {
            'title': 'GDPR/LGPD',
            'status': 'success' if stats['compliance']['gdpr'] else 'error',
            'items': [],
        },
        'ccpa': {
            'title': 'CCPA',
            'status': 'success' if stats['compliance']['ccpa'] else 'warning',
            'items': [],
        },
        'cookies': {
            'title': 'Configuração de Cookies',
            'status': 'success',
            'items': [],
        },
        'policies': {
            'title': 'Políticas e Termos',
            'status': 'success',
            'items': [],
        },
    }
    
    # Verificações GDPR/LGPD
    if not stats['policies']['privacy_policy']:
        compliance_checks['gdpr']['status'] = 'error'
        compliance_checks['gdpr']['items'].append({
            'status': 'error',
            'text': 'Política de Privacidade não configurada',
            'fix_url': reverse('compliance_settings')
        })
    
    if not stats['policies']['cookie_policy']:
        compliance_checks['gdpr']['status'] = 'error' if compliance_checks['gdpr']['status'] != 'error' else 'error'
        compliance_checks['gdpr']['items'].append({
            'status': 'error',
            'text': 'Política de Cookies não configurada',
            'fix_url': reverse('compliance_settings') + '#cookies'
        })
    
    # Verificações CCPA
    if stats['compliance']['ccpa'] and not compliance_settings.ccpa_do_not_sell_link:
        compliance_checks['ccpa']['status'] = 'warning'
        compliance_checks['ccpa']['items'].append({
            'status': 'warning',
            'text': 'Link "Não Vender Minhas Informações" não configurado',
            'fix_url': reverse('compliance_settings') + '#ccpa'
        })
    
    # Verificações de Cookies
    if not stats['cookies']['preferences']:
        compliance_checks['cookies']['status'] = 'warning'
        compliance_checks['cookies']['items'].append({
            'status': 'warning',
            'text': 'Preferências de cookies não estão sendo salvas',
            'fix_url': reverse('compliance_settings') + '#cookies'
        })
    
    # Verificações de Políticas
    if not all(stats['policies'].values()):
        compliance_checks['policies']['status'] = 'error'
        missing_policies = []
        
        if not stats['policies']['privacy_policy']:
            missing_policies.append('Política de Privacidade')
        if not stats['policies']['terms_of_service']:
            missing_policies.append('Termos de Serviço')
        if not stats['policies']['cookie_policy']:
            missing_policies.append('Política de Cookies')
            
        compliance_checks['policies']['items'].append({
            'status': 'error',
            'text': f'Documentos obrigatórios faltando: {", ".join(missing_policies)}',
            'fix_url': reverse('compliance_settings')
        })
    
    context = {
        'compliance_settings': compliance_settings,
        'stats': stats,
        'compliance_checks': compliance_checks,
        'title': 'Painel de Conformidade',
        'active_tab': 'dashboard',
    }
    return render(request, 'dashboard/compliance/dashboard.html', context)

@login_required
@permission_required('settings.change_compliancesettings')
def compliance_settings(request):
    """Edita as configurações de conformidade"""
    compliance_settings = ComplianceSettings.objects.first()
    
    if request.method == 'POST':
        form = ComplianceSettingsForm(
            request.POST, 
            instance=compliance_settings
        )
        
        if form.is_valid():
            form.save()
            messages.success(request, 'Configurações de conformidade atualizadas com sucesso!')
            return redirect('compliance_dashboard')
    else:
        form = ComplianceSettingsForm(instance=compliance_settings)
    
    return render(request, 'dashboard/compliance/settings.html', {
        'form': form,
        'title': 'Configurações de Conformidade',
        'active_tab': 'settings',
    })

@login_required
@permission_required('settings.view_datarequest')
def data_requests(request):
    """Lista todas as solicitações de dados"""
    data_requests = DataRequest.objects.all().order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status')
    if status_filter:
        data_requests = data_requests.filter(status=status_filter)
    
    # Paginação
    paginator = Paginator(data_requests, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'title': 'Solicitações de Dados',
        'active_tab': 'data_requests',
    }
    return render(request, 'dashboard/compliance/data_requests.html', context)

@login_required
@permission_required('settings.view_datarequest')
def data_request_detail(request, pk):
    """Detalhes de uma solicitação de dados"""
    data_request = get_object_or_404(DataRequest, pk=pk)
    
    # Formulário de resposta (apenas para administradores)
    response_form = None
    if request.user.has_perm('settings.change_datarequest'):
        if request.method == 'POST':
            response_form = DataRequestResponseForm(
                request.POST, 
                instance=data_request
            )
            
            if response_form.is_valid():
                response_form.save()
                messages.success(request, 'Resposta enviada com sucesso!')
                return redirect('data_request_detail', pk=pk)
        else:
            response_form = DataRequestResponseForm(instance=data_request)
    
    return render(request, 'dashboard/compliance/data_request_detail.html', {
        'data_request': data_request,
        'response_form': response_form,
        'title': f'Solicitação #{data_request.id} - {data_request.get_request_type_display()}',
        'active_tab': 'data_requests',
    })

@login_required
def my_data_requests(request):
    """Lista as solicitações de dados do usuário atual"""
    data_requests = DataRequest.objects.filter(user=request.user).order_by('-created_at')
    
    # Filtros
    status_filter = request.GET.get('status')
    if status_filter:
        data_requests = data_requests.filter(status=status_filter)
    
    # Paginação
    paginator = Paginator(data_requests, 10)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    return render(request, 'dashboard/compliance/my_data_requests.html', {
        'page_obj': page_obj,
        'status_filter': status_filter,
        'title': 'Minhas Solicitações de Dados',
        'active_tab': 'my_requests',
    })

@login_required
def request_my_data(request, request_type):
    """Solicita os dados do usuário"""
    if request.method == 'POST':
        form = DataRequestForm(
            request.POST, 
            user=request.user,
            initial={'request_type': request_type}
        )
        
        if form.is_valid():
            data_request = form.save(commit=False)
            data_request.user = request.user
            data_request.status = 'pending'
            data_request.save()
            
            # Aqui você pode adicionar lógica para processar a solicitação
            # Exemplo: enviar email para o administrador, processar em background, etc.
            
            messages.success(request, 'Sua solicitação foi enviada com sucesso! Entraremos em contato em breve.')
            return redirect('my_data_requests')
    else:
        form = DataRequestForm(
            user=request.user,
            initial={'request_type': request_type}
        )
    
    request_types = {
        'access': 'Acesso aos Meus Dados',
        'deletion': 'Excluir Meus Dados',
        'rectification': 'Corrigir Meus Dados',
        'portability': 'Solicitar Portabilidade de Dados',
    }
    
    return render(request, 'dashboard/compliance/request_my_data.html', {
        'form': form,
        'request_type': request_type,
        'request_type_display': request_types.get(request_type, 'Solicitação de Dados'),
        'title': f'Solicitar {request_types.get(request_type, "Dados")}',
        'active_tab': 'my_requests',
    })

# Views Públicas

def privacy_policy(request):
    """Exibe a política de privacidade"""
    compliance_settings = ComplianceSettings.objects.first()
    
    if not compliance_settings or not compliance_settings.privacy_policy:
        messages.warning(request, 'Política de privacidade não configurada.')
        return redirect('home')
    
    return render(request, 'compliance/privacy_policy.html', {
        'compliance_settings': compliance_settings,
        'title': 'Política de Privacidade',
    })

def terms_of_service(request):
    """Exibe os termos de serviço"""
    compliance_settings = ComplianceSettings.objects.first()
    
    if not compliance_settings or not compliance_settings.terms_of_service:
        messages.warning(request, 'Termos de serviço não configurados.')
        return redirect('home')
    
    return render(request, 'compliance/terms_of_service.html', {
        'compliance_settings': compliance_settings,
        'title': 'Termos de Serviço',
    })

def cookie_policy(request):
    """Exibe a política de cookies"""
    compliance_settings = ComplianceSettings.objects.first()
    
    if not compliance_settings or not compliance_settings.cookie_policy:
        messages.warning(request, 'Política de cookies não configurada.')
        return redirect('home')
    
    return render(request, 'compliance/cookie_policy.html', {
        'compliance_settings': compliance_settings,
        'title': 'Política de Cookies',
    })

@xframe_options_exempt
def cookie_settings(request):
    """Exibe as configurações de cookies"""
    compliance_settings = ComplianceSettings.objects.first()
    
    if request.method == 'POST':
        form = CookieConsentForm(request.POST)
        
        if form.is_valid():
            # Aqui você pode salvar as preferências de cookies
            response = JsonResponse({
                'status': 'success',
                'message': 'Preferências de cookies salvas com sucesso!'
            })
            
            # Configura os cookies com base nas preferências
            cookie_domain = getattr(settings, 'SESSION_COOKIE_DOMAIN', None)
            expires = (timezone.now() + timezone.timedelta(days=365)).strftime('%a, %d %b %Y %H:%M:%S GMT')
            
            # Cookie necessário (sempre ativo)
            response.set_cookie(
                'cookie_consent_necessary',
                'true',
                domain=cookie_domain,
                expires=expires,
                secure=request.is_secure(),
                httponly=True,
                samesite='Lax'
            )
            
            # Outros cookies
            for cookie_type in ['preferences', 'analytics', 'marketing']:
                value = 'true' if form.cleaned_data.get(cookie_type) else 'false'
                response.set_cookie(
                    f'cookie_consent_{cookie_type}',
                    value,
                    domain=cookie_domain,
                    expires=expires,
                    secure=request.is_secure(),
                    httponly=True,
                    samesite='Lax'
                )
            
            return response
    else:
        # Carrega as preferências atuais dos cookies
        initial = {
            'necessary': True,  # Sempre necessário
            'preferences': request.COOKIES.get('cookie_consent_preferences') == 'true',
            'analytics': request.COOKIES.get('cookie_consent_analytics') == 'true',
            'marketing': request.COOKIES.get('cookie_consent_marketing') == 'true',
        }
        form = CookieConsentForm(initial=initial)
    
    # Se for uma requisição AJAX, retorna o formulário como HTML
    if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
        form_html = render_to_string('compliance/partials/cookie_settings_form.html', {
            'form': form,
            'compliance_settings': compliance_settings,
        }, request=request)
        return JsonResponse({'form': form_html})
    
    # Se for um iframe, renderiza apenas o conteúdo
    if 'iframe' in request.GET:
        return render(request, 'compliance/partials/cookie_settings_modal.html', {
            'form': form,
            'compliance_settings': compliance_settings,
        })
    
    # Se for uma requisição normal, redireciona para a página inicial
    return redirect('home')

def ccpa_opt_out(request):
    """Página de opt-out do CCPA"""
    compliance_settings = ComplianceSettings.objects.first()
    
    if not compliance_settings or not compliance_settings.is_ccpa_compliant:
        messages.warning(request, 'Recurso de opt-out não disponível.')
        return redirect('home')
    
    if request.method == 'POST':
        # Aqui você pode processar o opt-out
        # Por exemplo, registrar a preferência do usuário
        
        # Configura um cookie para lembrar a escolha
        response = redirect('ccpa_opt_out_confirmation')
        response.set_cookie(
            'ccpa_opt_out',
            'true',
            max_age=365 * 24 * 60 * 60,  # 1 ano
            secure=request.is_secure(),
            httponly=True,
            samesite='Lax'
        )
        
        # Desativa o rastreamento para este usuário
        # (implemente conforme necessário)
        
        return response
    
    return render(request, 'compliance/ccpa_opt_out.html', {
        'compliance_settings': compliance_settings,
        'title': 'Não Vender Minhas Informações Pessoais',
    })

def ccpa_opt_out_confirmation(request):
    """Página de confirmação de opt-out do CCPA"""
    compliance_settings = ComplianceSettings.objects.first()
    
    if not compliance_settings or not compliance_settings.is_ccpa_compliant:
        messages.warning(request, 'Recurso de opt-out não disponível.')
        return redirect('home')
    
    return render(request, 'compliance/ccpa_opt_out_confirmation.html', {
        'compliance_settings': compliance_settings,
        'title': 'Sua escolha foi salva',
    })

# API Views

@csrf_exempt
@require_http_methods(["POST"])
def api_track_consent(request):
    """API para rastrear o consentimento de cookies"""
    try:
        data = json.loads(request.body)
        
        # Aqui você pode salvar o consentimento no banco de dados
        # Exemplo:
        # consent = CookieConsent.objects.create(
        #     session_key=request.session.session_key,
        #     user_agent=request.META.get('HTTP_USER_AGENT'),
        #     ip_address=request.META.get('REMOTE_ADDR'),
        #     preferences=data.get('preferences', {})
        # )
        
        return JsonResponse({'status': 'success'})
    except json.JSONDecodeError:
        return JsonResponse({'status': 'error', 'message': 'Invalid JSON'}, status=400)
    except Exception as e:
        logger.error(f"Erro ao rastrear consentimento: {e}", exc_info=True)
        return JsonResponse({'status': 'error', 'message': str(e)}, status=500)

@csrf_exempt
@require_http_methods(["POST"])
def api_data_request(request):
    """API para solicitações de dados (GDPR/LGPD/CCPA)"""
    try:
        data = json.loads(request.body)
        request_type = data.get('request_type')
        email = data.get('email')
        
        if not request_type or not email:
            return JsonResponse(
                {'status': 'error', 'message': 'Missing required fields'}, 
                status=400
            )
        
        # Verifica se o usuário está autenticado
        user = request.user if request.user.is_authenticated else None
        
        # Cria a solicitação de dados
        data_request = DataRequest.objects.create(
            user=user,
            email=email,
            request_type=request_type,
            description=data.get('description', ''),
            status='pending'
        )
        
        # Aqui você pode adicionar lógica para processar a solicitação
        # Exemplo: enviar email de confirmação, processar em background, etc.
        
        return JsonResponse({
            'status': 'success',
            'request_id': str(data_request.id),
            'message': 'Sua solicitação foi recebida e está sendo processada.'
        })
        
    except json.JSONDecodeError:
        return JsonResponse(
            {'status': 'error', 'message': 'Invalid JSON'}, 
            status=400
        )
    except Exception as e:
        logger.error(f"Erro ao processar solicitação de dados: {e}", exc_info=True)
        return JsonResponse(
            {'status': 'error', 'message': str(e)}, 
            status=500
        )
