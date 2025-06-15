from django.shortcuts import render, get_object_or_404, redirect
from django.views.generic import DetailView
from django.contrib import messages
from django.utils import timezone
from .models import Coupon

class CouponDetailView(DetailView):
    model = Coupon
    template_name = 'coupons/coupon_detail_public.html'
    context_object_name = 'coupon'
    
    def get_queryset(self):
        # Apenas cupons ativos e não expirados
        queryset = super().get_queryset()
        return queryset.filter(is_active=True)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['now'] = timezone.now()
        
        # Adicionar cupons relacionados (mesma categoria, excluindo o atual)
        if hasattr(self.object, 'category') and self.object.category:
            related_coupons = Coupon.objects.filter(
                category=self.object.category,
                is_active=True
            ).exclude(
                pk=self.object.pk
            )[:6]  # Limita a 6 cupons relacionados
            context['related_coupons'] = related_coupons
        
        return context

def coupon_redirect(request, pk):
    """Redireciona para o link do cupom e registra o clique"""
    coupon = get_object_or_404(Coupon, pk=pk, is_active=True)
    
    # Verifica se o cupom expirou
    if coupon.has_expiry and coupon.expiry_date < timezone.now().date():
        coupon.is_active = False
        coupon.save()
        messages.warning(request, 'Este cupom expirou e foi desativado.')
        return redirect('coupons_public:coupon_public_list')
    
    # Incrementa o contador de cliques
    coupon.click_count += 1
    coupon.save()
    
    # Obtém a URL de redirecionamento
    redirect_url = coupon.direct_link or coupon.product_link
    
    if not redirect_url:
        messages.error(request, 'Não foi possível encontrar o link de redirecionamento.')
        return redirect('coupons_public:coupon_public_list')
    
    # Verifica se o usuário já viu a página de redirecionamento
    seen_redirect = request.session.get(f'seen_redirect_{pk}', False)
    
    if not seen_redirect:
        # Marca como visto e mostra a página de redirecionamento
        request.session[f'seen_redirect_{pk}'] = True
        return render(request, 'coupons/coupon_redirect.html', {
            'coupon': coupon,
            'redirect_url': redirect_url
        })
    else:
        # Redireciona diretamente se já viu a página
        return redirect(redirect_url)
