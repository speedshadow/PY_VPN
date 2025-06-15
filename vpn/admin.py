from django.contrib import admin
from .models import VPN

@admin.register(VPN)
class VPNAdmin(admin.ModelAdmin):
    list_display = ('name', 'based_country', 'keep_logs', 'num_servers', 'price', 'show_on_homepage')
    list_filter = ('show_on_homepage', 'keep_logs', 'based_country', 'categories')
    search_fields = ('name',)
    filter_horizontal = ('categories',)

# Register your models here.
