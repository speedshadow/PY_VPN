from django.contrib import admin
from .models import BlogPost

@admin.register(BlogPost)
class BlogPostAdmin(admin.ModelAdmin):
    list_display = ('title', 'author', 'published', 'published_date')
    list_filter = ('published',)
    search_fields = ('title', 'slug')

# Register your models here.
