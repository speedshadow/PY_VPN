from django.shortcuts import render, get_object_or_404, redirect
from django.db.models import Q
from django.utils import timezone
from django.contrib import messages
from .models import Coupon
from categories.models import Category

from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

def coupon_public_list(request):
    """Exibe a lista de cupons ativos"""
    # Filtra os cupons ativos e não expirados
    now = timezone.now()
    coupons = Coupon.objects.filter(
        is_active=True
    ).filter(
        Q(expiry_date__isnull=True) |  # Cupons sem data de expiração
        Q(expiry_date__gte=now)        # Ou com data de expiração no futuro
    ).select_related('category').order_by('-created_at')
    
    # Aplicar filtro de busca se houver
    query = request.GET.get('q', '')
    if query:
        coupons = coupons.filter(
            Q(product_name__icontains=query) |
            Q(description__icontains=query) |
            Q(coupon_code__icontains=query)
        )
    
    # Paginação
    page = request.GET.get('page', 1)
    paginator = Paginator(coupons, 12)  # 12 cupons por página
    
    try:
        page_obj = paginator.page(page)
    except PageNotAnInteger:
        page_obj = paginator.page(1)
    except EmptyPage:
        page_obj = paginator.page(paginator.num_pages)
    
    # Obter todas as categorias ordenadas por nome
    categories = Category.objects.all().order_by('name')
    
    context = {
        'coupons': page_obj,  # Envia a página atual
        'page_obj': page_obj,  # Para compatibilidade com o template
        'categories': categories,
        'total_coupons': coupons.count(),
        'query': query,  # Para manter o termo de busca no input
    }
    
    return render(request, 'coupons/coupon_list_public.html', context)

def coupon_public_detail(request, pk):
    """Exibe os detalhes de um cupom específico"""
    coupon = get_object_or_404(
        Coupon.objects.select_related('category'),
        pk=pk,
        is_active=True
    )
    
    # Verificar se o cupom expirou
    if coupon.has_expiry and coupon.expiry_date < timezone.now().date():
        messages.warning(request, 'Este cupom expirou e não está mais disponível.')
        return redirect('coupons_public:coupon_public_list')
    
    # Cupons relacionados (mesma categoria, excluindo o atual)
    related_coupons = Coupon.objects.filter(
        category=coupon.category,
        is_active=True
    ).exclude(
        pk=coupon.pk
    ).select_related('category')[:6]  # Limita a 6 cupons relacionados
    
    # Incrementar contador de visualizações
    coupon.views_count = coupon.views_count + 1 if hasattr(coupon, 'views_count') else 1
    coupon.save(update_fields=['views_count'])
    
    context = {
        'coupon': coupon,
        'related_coupons': related_coupons,
        'now': timezone.now()  # Adiciona a data/hora atual para verificação de validade
    }
    
    return render(request, 'coupons/coupon_detail_public.html', context)

def coupon_redirect_view(request, pk):
    """Redireciona para o link do cupom e registra o clique"""
    coupon = get_object_or_404(Coupon, pk=pk, is_active=True)
    
    # Verificar se o cupom expirou
    if coupon.has_expiry and coupon.expiry_date < timezone.now().date():
        coupon.is_active = False
        coupon.save(update_fields=['is_active'])
        messages.warning(request, 'Este cupom expirou e foi desativado.')
        return redirect('coupons_public:coupon_public_list')
    
    # Incrementar contador de cliques
    coupon.click_count = coupon.click_count + 1 if hasattr(coupon, 'click_count') else 1
    coupon.save(update_fields=['click_count'])
    
    # Redirecionar para o link apropriado
    redirect_url = coupon.direct_link or coupon.product_link
    
    if not redirect_url:
        messages.error(request, 'Não foi possível encontrar o link de redirecionamento.')
        return redirect('coupons_public:coupon_public_detail', pk=pk)
    
    return redirect(redirect_url)
