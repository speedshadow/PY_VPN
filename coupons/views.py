from django.shortcuts import render, redirect, get_object_or_404, reverse
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.utils import timezone
from django.db.models import Q
from .models import Coupon
from .forms import CouponForm

@login_required(login_url='/admin/login/')
@permission_required('coupons.view_coupon', raise_exception=True)
def coupon_list(request):
    """Lista todos os cupons"""
    query = request.GET.get('q', '')
    
    coupons = Coupon.objects.all()
    
    if query:
        coupons = coupons.filter(
            Q(product_name__icontains=query) |
            Q(coupon_code__icontains=query)
        )
    
    context = {
        'coupons': coupons,
        'query': query,
        'active_coupons': coupons.filter(is_active=True).count(),
        'expired_coupons': coupons.filter(expiry_date__lt=timezone.now()).count(),
    }
    return render(request, 'dashboard/coupons/list.html', context)

@login_required(login_url='/admin/login/')
@permission_required('coupons.add_coupon', raise_exception=True)
def coupon_create(request):
    """Cria um novo cupom"""
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.created_by = request.user
            coupon.save()
            messages.success(request, 'Cupom criado com sucesso!')
            return redirect('coupons:list')
    else:
        form = CouponForm()
    
    context = {
        'form': form,
        'title': 'Adicionar Novo Cupom',
        'submit_text': 'Criar Cupom',
    }
    return render(request, 'dashboard/coupons/form.html', context)

@login_required(login_url='/admin/login/')
@permission_required('coupons.change_coupon', raise_exception=True)
def coupon_edit(request, pk):
    """Edita um cupom existente"""
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            coupon = form.save(commit=False)
            coupon.updated_by = request.user
            coupon.save()
            messages.success(request, 'Cupom atualizado com sucesso!')
            return redirect('coupons:list')
    else:
        form = CouponForm(instance=coupon)
    
    context = {
        'form': form,
        'coupon': coupon,
        'title': f'Editar Cupom: {coupon.product_name}',
        'submit_text': 'Atualizar Cupom',
    }
    return render(request, 'dashboard/coupons/form.html', context)

@login_required(login_url='/admin/login/')
@permission_required('coupons.delete_coupon', raise_exception=True)
def coupon_delete(request, pk):
    """Remove um cupom"""
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        coupon.delete()
        messages.success(request, 'Cupom removido com sucesso!')
        return redirect('coupons:list')
    
    context = {
        'coupon': coupon,
        'title': 'Confirmar Exclusão',
        'message': f'Tem certeza que deseja excluir o cupom "{coupon.product_name}"?',
    }
    return render(request, 'dashboard/coupons/confirm_delete.html', context)

@login_required(login_url='/admin/login/')
@permission_required('coupons.change_coupon', raise_exception=True)
def toggle_coupon_status(request, pk):
    """Ativa/desativa um cupom"""
    coupon = get_object_or_404(Coupon, pk=pk)
    
    if request.method == 'POST':
        coupon.is_active = not coupon.is_active
        coupon.save()
        
        status = 'ativado' if coupon.is_active else 'desativado'
        messages.success(request, f'Cupom {status} com sucesso!')
    
    return redirect('coupons:list')
