from django.contrib import admin
from .models_faq import FAQ

@admin.register(FAQ)
class FAQAdmin(admin.ModelAdmin):
    list_display = ("question", "order")
    list_editable = ("order",)
    search_fields = ("question", "answer")
    ordering = ("order", "id")
