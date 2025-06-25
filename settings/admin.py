from django.contrib import admin
from .models import SiteSettings
from .models_compliance import ComplianceSettings, DataRequest
from django.db import OperationalError, ProgrammingError

# --- Singleton Admin Pattern ---
# This ensures that only one instance of the settings object can be created.
class SingletonModelAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        # Deny permission to add new objects if one already exists.
        # Use a try-except block to prevent crashes if the table doesn't exist yet (e.g., during migrations).
        try:
            return not self.model.objects.exists()
        except (OperationalError, ProgrammingError):
            # The table doesn't exist yet, so we can't check.
            # Allow adding it for now.
            return True

    def has_delete_permission(self, request, obj=None):
        # It's generally a bad idea to delete the settings object.
        return False

# --- Site Settings Admin ---
@admin.register(SiteSettings)
class SiteSettingsAdmin(SingletonModelAdmin):
    fieldsets = (
        ('Configurações Básicas', {
            'fields': ('site_name', 'site_url', 'contact_email', 'favicon')
        }),
        ('Configurações de SEO', {
            'classes': ('collapse',),
            'fields': ('seo_title', 'seo_description', 'seo_keywords', 'google_analytics_id', 'google_site_verification')
        }),
        ('Modo Manutenção', {
            'classes': ('collapse',),
            'fields': ('maintenance_mode', 'maintenance_message')
        }),
    )

    # The __init__ method that automatically created a settings object was removed.
    # It caused the Docker build to fail by querying the database before migrations.
    # The first SiteSettings object must now be created manually in the Django admin.

# --- Compliance Settings Admin ---
@admin.register(ComplianceSettings)
class ComplianceSettingsAdmin(SingletonModelAdmin):
    fieldsets = (
        ('Conformidade Geral (GDPR/LGPD)', {
            'fields': (
                'is_gdpr_compliant', 'data_controller', 'data_protection_officer',
                'dpo_email', 'data_retention_days'
            )
        }),
        ('Políticas (Conteúdo)', {
            'classes': ('collapse',),
            'fields': ('privacy_policy_content', 'terms_of_service_content', 'cookie_policy_content')
        }),
        ('Gestão de Cookies', {
            'classes': ('collapse',),
            'fields': ('cookie_banner_text', 'cookie_banner_button_text')
        }),
    )

    # The __init__ method that automatically created a settings object was removed.
    # It caused the Docker build to fail by querying the database before migrations.
    # The first ComplianceSettings object must now be created manually in the Django admin.

# --- Data Request Admin ---
@admin.register(DataRequest)
class DataRequestAdmin(admin.ModelAdmin):
    list_display = ('user', 'request_type', 'status', 'created_at', 'processed_by')
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('user__username', 'user__email', 'description')
    readonly_fields = ('user', 'request_type', 'description', 'created_at', 'updated_at', 'processed_by', 'processed_at')
    fieldsets = (
        ('Detalhes da Solicitação', {
            'fields': ('user', 'request_type', 'status', 'description', 'created_at')
        }),
        ('Resposta da Administração', {
            'fields': ('response', 'processed_by', 'processed_at')
        }),
    )

    def save_model(self, request, obj, form, change):
        # Automatically set the user who processed the request
        if 'response' in form.changed_data or 'status' in form.changed_data:
            if obj.status != 'PENDING' and not obj.processed_by:
                obj.processed_by = request.user
                from django.utils import timezone
                obj.processed_at = timezone.now()
        super().save_model(request, obj, form, change)

    def has_add_permission(self, request):
        # Data requests should be created by users, not admins.
        return False

    def has_delete_permission(self, request, obj=None):
        # Keep a record of all data requests.
        return False
