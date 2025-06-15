from django.contrib import admin
from django import forms
from django.db import models
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.utils import timezone
from .models import Coupon

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
    # Campos exibidos na lista
    list_display = (
        'product_name_with_code', 
        'is_active',
        'status_badge',
        'expiry_status',
        'discount_display',
        'click_count',
        'created_at_formatted',
        'actions_column'
    )
    
    # Filtros
    list_filter = (IsExpiredFilter, 'is_active', 'has_expiry', 'created_at')
    
    # Campos de busca
    search_fields = ('product_name', 'coupon_code', 'product_link', 'direct_link')
    
    # Links rápidos
    list_display_links = ('product_name_with_code',)
    
    # Campos editáveis na lista
    list_editable = ('is_active',)
    
    # Paginação
    list_per_page = 25
    
    # Hierarquia de datas
    date_hierarchy = 'created_at'
    fieldsets = (
        ('Informações do Produto', {
            'fields': ('product_name', 'product_link', 'product_image')
        }),
        ('Detalhes do Cupom', {
            'fields': ('coupon_code', 'direct_link', 'discount_amount')
        }),
        ('Validade', {
            'fields': ('has_expiry', 'expiry_date')
        }),
        ('Conteúdo Adicional', {
            'classes': ('collapse',),
            'fields': ('terms', 'instructions')
        }),
        ('Status e Métricas', {
            'fields': ('is_active', 'click_count')
        }),
        ('Metadados', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at', 'created_by', 'updated_by')
        }),
    )
    
    # Campos somente leitura
    readonly_fields = ('created_at', 'updated_at', 'created_by', 'updated_by', 'click_count')
    
    # Ordenação padrão
    ordering = ('-created_at',)
    
    # Campos para pré-carregar
    autocomplete_fields = ['created_by', 'updated_by']
    
    # Formulário personalizado
    formfield_overrides = {
        models.TextField: {'widget': forms.Textarea(attrs={'rows': 4, 'cols': 60})},
    }
    
    def save_model(self, request, obj, form, change):
        if not obj.pk:
            obj.created_by = request.user
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def product_name_with_code(self, obj):
        name = f'<strong>{obj.product_name}</strong>'
        if obj.coupon_code:
            name += f'<div class="text-xs text-gray-500">Código: {obj.coupon_code}</div>'
        if obj.direct_link:
            name += f'<div class="text-xs"><a href="{obj.direct_link}" target="_blank" class="text-blue-600 hover:underline">Link direto</a></div>'
        return mark_safe(name)
    product_name_with_code.short_description = 'Produto'
    product_name_with_code.admin_order_field = 'product_name'
    
    def discount_display(self, obj):
        if obj.discount_amount:
            return f'{obj.discount_amount}% OFF'
        return '-'
    discount_display.short_description = 'Desconto'
    discount_display.admin_order_field = 'discount_amount'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_at_formatted.short_description = 'Criado em'
    created_at_formatted.admin_order_field = 'created_at'
    
    def status_badge(self, obj):
        if not obj.is_active:
            return mark_safe('<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-red-100 text-red-800">Inativo</span>')
        elif obj.is_expired:
            return mark_safe('<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-yellow-100 text-yellow-800">Expirado</span>')
        else:
            return mark_safe('<span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Ativo</span>')
    status_badge.short_description = 'Status'
    status_badge.admin_order_field = 'is_active'
    
    def expiry_status(self, obj):
        if not obj.has_expiry:
            return 'Sem data de expiração'
        if obj.is_expired:
            return f'Expirou em {obj.expiry_date.strftime("%d/%m/%Y")}'
        return f'Válido até {obj.expiry_date.strftime("%d/%m/%Y")}'
    expiry_status.short_description = 'Validade'
    expiry_status.admin_order_field = 'expiry_date'
    
    def created_at_formatted(self, obj):
        return obj.created_at.strftime('%d/%m/%Y %H:%M')
    created_at_formatted.short_description = 'Criado em'
    created_at_formatted.admin_order_field = 'created_at'
    
    def actions_column(self, obj):
        edit_url = reverse('admin:coupons_coupon_change', args=[obj.id])
        return mark_safe(f'''
            <div class="flex space-x-2">
                <a href="{edit_url}" class="text-indigo-600 hover:text-indigo-900" title="Editar">
                    <svg class="h-5 w-5" fill="none" viewBox="0 0 24 24" stroke="currentColor">
                        <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M11 5H6a2 2 0 00-2 2v11a2 2 0 002 2h11a2 2 0 002-2v-5m-1.414-9.414a2 2 0 112.828 2.828L11.828 15H9v-2.828l8.586-8.586z" />
                    </svg>
                </a>
            </div>
        ''')
    actions_column.short_description = 'Ações'
    actions_column.allow_tags = True
    
    class Media:
        css = {
            'all': ('css/admin/coupon_admin.css',)
        }
        js = ('js/admin/coupon_admin.js',)
        
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        return qs.select_related('created_by', 'updated_by')
