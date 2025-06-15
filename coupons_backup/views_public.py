from django.shortcuts import render
from .models import Coupon

def coupon_public_list(request):
    coupons = Coupon.objects.filter(is_active=True)
    return render(request, 'coupons/coupon_list_public.html', {'coupons': coupons})
