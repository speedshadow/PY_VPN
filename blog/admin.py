from django.contrib import admin
from .models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'author', 'published', 'featured', 'updated_at')
    list_filter = ('published', 'author')
    search_fields = ('title', 'slug', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-updated_at',)

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'featured', 'featured_image')
        }),
        ('Conteúdo', {
            'fields': ('content',)
        }),
        ('Publicação', {
            'fields': ('published', 'published_date')
        }),
        ('Metadados', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')
