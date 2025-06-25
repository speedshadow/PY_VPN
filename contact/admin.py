from django.contrib import admin
from .models import ContactMessage

from django.utils.html import format_html

@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    list_display = ("name", "email", "subject", "created_at", "unread_badge")
    search_fields = ("name", "email", "subject", "message")
    readonly_fields = ("name", "email", "subject", "message", "created_at")
    ordering = ("-created_at",)

    def unread_badge(self, obj):
        if not obj.is_read:
            return format_html(
                '<span style="color: white; background: #e53e3e; border-radius: 6px; padding: 2px 8px; font-weight: bold;">NEW</span>'
            )
        return ""
    unread_badge.short_description = "Status"
