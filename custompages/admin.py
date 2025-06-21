from django.contrib import admin
from .models import CustomPage
from .forms import CustomPageForm

@admin.register(CustomPage)
class CustomPageAdmin(admin.ModelAdmin):
    form = CustomPageForm
    list_display = ('title', 'slug', 'is_active', 'updated_at')
    search_fields = ('title', 'slug', 'content')
    list_filter = ('is_active',)
    prepopulated_fields = {'slug': ('title',)}
    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'is_active')
        }),
        ('Conteúdo da Página', {
            'fields': ('content',)
        }),
        ('Metadados', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
