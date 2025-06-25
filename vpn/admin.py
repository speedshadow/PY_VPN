from django.contrib import admin
from .models import VPN, VPNSpeed
from .forms import VPNForm

class VPNSpeedInline(admin.TabularInline):
    model = VPNSpeed
    extra = 1 # Number of empty forms to display
    fields = ('country', 'speed')
    verbose_name = "Velocidade por País"
    verbose_name_plural = "Velocidades por País"

@admin.register(VPN)
class VPNAdmin(admin.ModelAdmin):
    form = VPNForm
    list_display = ('name', 'overall_rating', 'based_country', 'is_active', 'show_on_homepage')
    list_filter = ('is_active', 'show_on_homepage', 'keep_logs', 'based_country', 'categories')
    search_fields = ('name', 'slug', 'based_country')
    prepopulated_fields = {'slug': ('name',)}
    filter_horizontal = ('categories',)
    ordering = ('-updated_at',)

    fieldsets = (
        ('Informações Gerais', {
            'fields': ('name', 'slug', 'logo_upload', 'logo', 'affiliate_link', 'price', 'categories')
        }),
        ('Características', {
            'fields': ('based_country', 'num_servers', 'keep_logs', 'devices_supported') # 'speeds_by_country' removed
        }),
        ('Avaliações', {
            'fields': (
                'overall_rating', 
                ('security_rating', 'privacy_rating', 'speed_rating'),
                ('streaming_rating', 'torrenting_rating', 'additional_features_rating'),
                ('device_compatibility_rating', 'server_locations_rating', 'user_experience_rating')
            )
        }),
        ('Conteúdo', {
            'fields': ('pros', 'cons', 'full_review')
        }),
        ('Configurações de Exibição', {
            'fields': ('is_active', 'show_on_homepage')
        }),
        ('Metadados', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
    inlines = [VPNSpeedInline,]

# Register your models here.
