from django.contrib import admin
from .models import BlogPost, Category, Comment
from . import admin_faq

@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ("name", "slug")
    prepopulated_fields = {"slug": ("name",)}
    search_fields = ("name",)
    ordering = ("name",)

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'slug', 'author', 'category', 'published', 'featured', 'comments_enabled', 'updated_at')
    list_filter = ('published', 'author', 'category', 'comments_enabled')
    search_fields = ('title', 'slug', 'content', 'author')
    prepopulated_fields = {'slug': ('title',)}
    date_hierarchy = 'created_at'
    ordering = ('-updated_at',)

    fieldsets = (
        (None, {
            'fields': ('title', 'slug', 'author', 'category', 'featured', 'featured_image')
        }),
        ('Conteúdo', {
            'fields': ('content',)
        }),
        ('Publicação', {
            'fields': ('published', 'published_date', 'comments_enabled')
        }),
        ('Metadados', {
            'classes': ('collapse',),
            'fields': ('created_at', 'updated_at'),
        }),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(Comment)
class CommentAdmin(admin.ModelAdmin):
    list_display = ('author_name', 'post', 'created_at', 'approved')
    list_filter = ('approved', 'created_at')
    search_fields = ('author_name', 'author_email', 'content')
    actions = ['approve_comments']

    def approve_comments(self, request, queryset):
        queryset.update(approved=True)
    approve_comments.short_description = "Approve selected comments"
