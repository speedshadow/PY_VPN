from django.contrib import admin
from .models import Analytics

@admin.register(Analytics)
class AnalyticsAdmin(admin.ModelAdmin):
    list_display = ('ip_address', 'event_type', 'is_bot', 'page_url', 'timestamp')
    list_filter = ('event_type', 'is_bot')
    search_fields = ('ip_address', 'page_url', 'user_agent')

# Register your models here.
