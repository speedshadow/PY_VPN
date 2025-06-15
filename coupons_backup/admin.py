from django.contrib import admin
from .models import Coupon

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    list_display = ('product_name', 'coupon_code', 'direct_link', 'has_expiry', 'expiry_date', 'is_active')
    list_filter = ('is_active', 'has_expiry')
    search_fields = ('product_name', 'coupon_code')

# Register your models here.
