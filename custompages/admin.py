from django.contrib import admin
from .models import CustomPage

@admin.register(CustomPage)
class CustomPageAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'is_active', 'created_at', 'updated_at')
    search_fields = ('title', 'slug')
    list_filter = ('is_active',)
