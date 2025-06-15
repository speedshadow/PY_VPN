from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from .models import Coupon
from .forms import CouponForm

@login_required(login_url='/admin/login/')
def coupon_list(request):
    coupons = Coupon.objects.all()
    return render(request, 'dashboard/coupon_list.html', {'coupons': coupons})

@login_required(login_url='/admin/login/')
def coupon_create(request):
    if request.method == 'POST':
        form = CouponForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('coupon_list')
    else:
        form = CouponForm()
    return render(request, 'dashboard/coupon_form.html', {'form': form, 'coupon': None})

@login_required(login_url='/admin/login/')
def coupon_edit(request, coupon_id):
    coupon = get_object_or_404(Coupon, pk=coupon_id)
    if request.method == 'POST':
        form = CouponForm(request.POST, instance=coupon)
        if form.is_valid():
            form.save()
            return redirect('coupon_list')
    else:
        form = CouponForm(instance=coupon)
    return render(request, 'dashboard/coupon_form.html', {'form': form, 'coupon': coupon})

@login_required(login_url='/admin/login/')
def coupon_delete(request, coupon_id):
    coupon = get_object_or_404(Coupon, pk=coupon_id)
    if request.method == 'POST':
        coupon.delete()
        return redirect('coupon_list')
    return render(request, 'dashboard/coupon_confirm_delete.html', {'coupon': coupon})
