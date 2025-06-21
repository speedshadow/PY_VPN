from django.contrib import admin
from django.db import models
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import Coupon
from .forms import CouponForm

class IsExpiredFilter(admin.SimpleListFilter):
    title = 'status de validade'
    parameter_name = 'is_expired'

    def lookups(self, request, model_admin):
        return (
            ('yes', 'Expirados'),
            ('no', 'Válidos'),
            ('no_date', 'Sem data de expiração'),
        )

    def queryset(self, request, queryset):
        today = timezone.now().date()
        if self.value() == 'yes':
            return queryset.filter(has_expiry=True, expiry_date__lt=today)
        if self.value() == 'no':
            return queryset.filter(
                models.Q(has_expiry=False) | 
                models.Q(has_expiry=True, expiry_date__gte=today)
            )
        if self.value() == 'no_date':
            return queryset.filter(has_expiry=False)

@admin.register(Coupon)
class CouponAdmin(admin.ModelAdmin):
    form = CouponForm
    list_display = (
        'product_name_with_code', 
        'category',
        'is_active',
        'status_badge',
        'expiry_status',
        'click_count',
        'views_count'
    )
    list_filter = (IsExpiredFilter, 'is_active', 'has_expiry', 'category', 'created_at')
    search_fields = ('product_name', 'coupon_code', 'description', 'category__name')
    list_display_links = ('product_name_with_code',)
    list_editable = ('is_active',)
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Informações Principais', {
            'fields': ('product_name', 'product_link', 'category', 'is_active')
        }),
        ('Detalhes do Cupom', {
            'fields': ('coupon_code', 'direct_link', 'discount_amount')
        }),
        ('Validade', {
            'fields': ('has_expiry', 'expiry_date')
        }),
        ('Conteúdo e Mídia', {
            'classes': ('collapse',),
            'fields': ('description', 'product_image', 'terms', 'instructions')
        }),
        ('Metadados (Automático)', {
            'classes': ('collapse',),
            'fields': ('views_count', 'click_count', 'created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    readonly_fields = ('views_count', 'click_count', 'created_at', 'updated_at', 'created_by', 'updated_by')
    ordering = ('-created_at',)
    autocomplete_fields = ['category', 'created_by', 'updated_by']
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def product_name_with_code(self, obj):
        name = f'<strong>{obj.product_name}</strong>'
        if obj.coupon_code:
            name += f'<div style="font-size: 0.9em; color: #555;">Código: {obj.coupon_code}</div>'
        if obj.direct_link:
            name += f'<div style="font-size: 0.9em;"><a href="{obj.direct_link}" target="_blank">Link direto</a></div>'
        return mark_safe(name)
    product_name_with_code.short_description = 'Produto'
    product_name_with_code.admin_order_field = 'product_name'
    
    def status_badge(self, obj):
        if not obj.is_active:
            style = 'background-color: #fbeaea; color: #c82333; padding: 3px 8px; border-radius: 12px; font-size: 0.9em;'
            return mark_safe(f'<span style="{style}">Inativo</span>')
        elif obj.is_expired:
            style = 'background-color: #fff3cd; color: #856404; padding: 3px 8px; border-radius: 12px; font-size: 0.9em;'
            return mark_safe(f'<span style="{style}">Expirado</span>')
        else:
            style = 'background-color: #d4edda; color: #155724; padding: 3px 8px; border-radius: 12px; font-size: 0.9em;'
            return mark_safe(f'<span style="{style}">Ativo</span>')
    status_badge.short_description = 'Status'
    
    def expiry_status(self, obj):
        if not obj.has_expiry:
            return 'Sem data de expiração'
        if obj.is_expired:
            return f'Expirou em {obj.expiry_date.strftime("%d/%m/%Y")}'
        return f'Válido até {obj.expiry_date.strftime("%d/%m/%Y")}'
    expiry_status.short_description = 'Validade'
    expiry_status.admin_order_field = 'expiry_date'
    
    class Media:
        css = {
            'all': ('admin/css/coupon_admin.css',)
        }
        js = ('admin/js/coupon_admin.js',)
        
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('created_by', 'updated_by', 'category')
