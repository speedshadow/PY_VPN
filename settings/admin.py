# settings/admin.py
from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.http import HttpResponseRedirect
from django.utils import timezone
from django.conf import settings as django_settings

# Model from settings/models.py
from .models import SiteSettings

# Models from settings/models_*.py
from .models_seo import SEOSettings, PageSEO, XMLSitemap
from .models_compliance import ComplianceSettings, DataRequest
from .models_customization import SiteCustomization, CustomCSS, CustomJavaScript

# Forms for models in models_*.py
# SiteSettingsAdmin will use the default ModelForm.
from .forms_seo import SEOSettingsForm, PageSEOForm, XMLSitemapForm
from .forms_compliance import ComplianceSettingsForm, DataRequestForm, DataRequestResponseForm
from .forms_customization import SiteCustomizationForm, CustomCSSForm, CustomJavaScriptForm

# Views for custom admin pages
from .views_https import https_setup_wizard

# --- SiteSettingsAdmin (adapted from existing admin.py) ---
@admin.register(SiteSettings)
class SiteSettingsAdmin(admin.ModelAdmin): # Does not use SingletonModelAdmin to preserve specific logic
    list_display = ('site_name', 'site_url', 'maintenance_mode', 'security_status_display_list', 'updated_at')
    list_editable = ('maintenance_mode',)
    # form = SiteSettingsForm # Not using this as it's too limited. Default ModelForm is better.
    
    # Define fieldsets based on the SiteSettings model structure
    fieldsets = (
        ('Informações Básicas', {'fields': ('site_name', 'site_url', 'contact_email', 'favicon')}),
        ('Configurações de SEO', {'fields': ('seo_title', 'seo_description', 'seo_keywords', 'google_analytics_id', 'google_site_verification')}),
        ('Configurações de Manutenção', {'fields': ('maintenance_mode', 'maintenance_message')}),
        ('Segurança - HTTPS e Cabeçalhos', {'fields': ('enable_https', 'enable_hsts', 'hsts_max_age', 'enable_xss_filter', 'enable_content_type_nosniff', 'enable_x_frame_options', 'x_frame_options')}),
        ('Configurações de Sessão', {'fields': ('session_cookie_secure', 'session_cookie_http_only', 'session_cookie_samesite', 'csrf_cookie_secure', 'csrf_cookie_http_only')}),
        ('Segurança de Senhas', {'fields': ('enable_2fa', 'password_min_length', 'password_require_uppercase', 'password_require_lowercase', 'password_require_number', 'password_require_special_char')}),
        ('Proteção contra Ataques (Django-Axes)', {'fields': ('axes_failure_limit', 'axes_cooloff_time', 'axes_lock_out_at_failure', 'axes_use_user_agent', 'axes_only_user_failure', 'axes_reset_on_success')}),
        ('Cabeçalhos de Segurança Avançados (JSON)', {'classes': ('collapse',), 'fields': ('security_headers',)}),
        ('Status de Segurança', {'classes': ('collapse',), 'fields': ('security_status_display_form',)}),
        ('Metadados', {'classes': ('collapse',), 'fields': ('created_at', 'updated_at')}),
    )
    
    readonly_fields = ('created_at', 'updated_at', 'security_status_display_form')

    def _get_security_status_html(self, obj):
        if not obj or not hasattr(obj, 'get_security_status'): return "N/A"
        status = obj.get_security_status()
        html_parts = []
        for key, value in status.items():
            icon = '✅' if value else '❌'
            label = key.replace('_', ' ').title().replace('Https', 'HTTPS').replace('Hsts', 'HSTS').replace('Xss', 'XSS')
            html_parts.append(f"<div>{icon} {label}</div>")
        return format_html("".join(html_parts))

    def security_status_display_list(self, obj):
        return self._get_security_status_html(obj)
    security_status_display_list.short_description = 'Status Segurança'

    def security_status_display_form(self, obj):
        return self._get_security_status_html(obj)
    security_status_display_form.short_description = 'Resumo Detalhado de Segurança'

    def has_add_permission(self, request):
        # SiteSettings model's save() method handles singleton logic.
        # This admin method ensures only one can be added via UI initially.
        return not SiteSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False # Prevent deletion

    def changelist_view(self, request, extra_context=None):
        # Redirect to the single object's change page if it exists
        if SiteSettings.objects.exists():
            obj = SiteSettings.objects.first()
            return HttpResponseRedirect(reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change', args=(obj.pk,)))
        return super().changelist_view(request, extra_context)
        
    def get_urls(self):
        urls = super().get_urls()
        custom_urls = [
            path('https-setup-wizard/', self.admin_site.admin_view(https_setup_wizard), name=f'{self.model._meta.app_label}_https_setup_wizard'),
        ]
        return custom_urls + urls

    class Media: # Ensure these static files exist or are created
        css = {'all': (f'{django_settings.STATIC_URL}admin/css/security_status.css',)}
        js = (f'{django_settings.STATIC_URL}admin/js/security_settings.js',)

# --- Generic Singleton Model Admin for other settings modules ---
class SingletonModelAdmin(admin.ModelAdmin):
    def has_add_permission(self, request):
        return not self.model.objects.exists()

    def has_delete_permission(self, request, obj=None):
        return False # Prevent deletion of singleton objects

    def changelist_view(self, request, extra_context=None):
        if self.model.objects.exists():
            obj = self.model.objects.first()
            return HttpResponseRedirect(reverse(f'admin:{self.model._meta.app_label}_{self.model._meta.model_name}_change', args=(obj.pk,)))
        return super().changelist_view(request, extra_context)

# --- SEO Settings ---
@admin.register(SEOSettings)
class SEOSettingsAdmin(SingletonModelAdmin):
    form = SEOSettingsForm
    fieldsets = (
        ('Meta Tags Globais', {'fields': ('meta_title', 'meta_description', 'meta_keywords', 'meta_author', 'meta_robots', 'canonical_url')}),
        ('Open Graph', {'fields': ('og_title', 'og_description', 'og_image')}),
        ('Twitter Cards', {'fields': ('twitter_card', 'twitter_site', 'twitter_creator')}),
        ('Dados Estruturados (JSON-LD)', {'fields': ('structured_data',)}),
        ('Sitemap Defaults', {'fields': ('sitemap_priority', 'sitemap_changefreq')}),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(PageSEO)
class PageSEOAdmin(admin.ModelAdmin):
    form = PageSEOForm
    list_display = ('page_type', 'meta_title', 'sitemap_include', 'sitemap_priority', 'updated_at')
    list_filter = ('page_type', 'sitemap_include')
    search_fields = ('page_type', 'meta_title', 'meta_description')

    fieldsets = (
        (None, {'fields': ('page_type',)}),
        ('Meta Tags', {'fields': ('meta_title', 'meta_description', 'meta_keywords', 'meta_robots', 'canonical_url')}),
        ('Open Graph', {'fields': ('og_title', 'og_description', 'og_image')}),
        ('Dados Estruturados (JSON-LD)', {'fields': ('structured_data',)}),
        ('Sitemap Config', {'fields': ('sitemap_include', 'sitemap_priority', 'sitemap_changefreq')}),
    )
    readonly_fields = ('created_at', 'updated_at')

    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        if obj:
            form.base_fields['page_type'].disabled = True
            form.base_fields['page_type'].help_text = "O tipo de página não pode ser alterado após a criação."
        return form

@admin.register(XMLSitemap)
class XMLSitemapAdmin(admin.ModelAdmin):
    form = XMLSitemapForm
    list_display = ('url', 'priority', 'changefreq', 'lastmod_display', 'is_active')
    list_filter = ('is_active', 'changefreq')
    search_fields = ('url',)
    def get_readonly_fields(self, request, obj=None):
        if obj:
            return ('created_at', 'updated_at', 'lastmod')
        return ()

    def lastmod_display(self, obj):
        return obj.lastmod.strftime("%Y-%m-%d %H:%M") if obj.lastmod else "-"
    lastmod_display.short_description = 'Última Modificação'

# --- Compliance Settings ---
@admin.register(ComplianceSettings)
class ComplianceSettingsAdmin(SingletonModelAdmin):
    form = ComplianceSettingsForm
    fieldsets = (
        ('GDPR/LGPD', {'fields': ('is_gdpr_compliant', 'data_controller', 'data_protection_officer', 'dpo_email', 'privacy_policy', 'terms_of_service', 'cookie_policy', 'data_retention_days')}),
        ('Cookies', {'fields': ('cookie_consent_enabled', 'cookie_consent_message', 'cookie_necessary', 'cookie_analytics', 'cookie_marketing', 'cookie_preferences')}),
        ('CCPA', {'fields': ('is_ccpa_compliant', 'ccpa_do_not_sell_link')}),
        ('Outras Conformidades', {'fields': ('age_restriction',)}),
        ('Auditoria', {'fields': ('last_audit_date', 'next_audit_date')}),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(DataRequest)
class DataRequestAdmin(admin.ModelAdmin):
    form = DataRequestForm # Default form for adding
    list_display = ('user_display', 'request_type', 'status', 'created_at_display', 'processed_by_display', 'processed_at_display')
    list_filter = ('status', 'request_type', 'created_at')
    search_fields = ('user__email', 'user__username', 'description', 'response')
    fieldsets = (
        ('Detalhes da Solicitação', {'fields': ('user', 'request_type', 'description', 'created_at')}),
        ('Resposta (Administrador)', {'fields': ('status', 'response')}),
    )

    def user_display(self, obj): return obj.user.get_full_name() or obj.user.username if obj.user else "N/A"
    user_display.short_description = 'Usuário'

    def processed_by_display(self, obj): return obj.processed_by.username if obj.processed_by else '-'
    processed_by_display.short_description = 'Processado Por'
    
    def created_at_display(self, obj): return obj.created_at.strftime("%Y-%m-%d %H:%M") if obj.created_at else '-'
    created_at_display.short_description = 'Criado Em'

    def processed_at_display(self, obj): return obj.processed_at.strftime("%Y-%m-%d %H:%M") if obj.processed_at else '-'
    processed_at_display.short_description = 'Processado Em'

    def get_form(self, request, obj=None, **kwargs):
        if obj: kwargs['form'] = DataRequestResponseForm # Use response form when editing
        else: kwargs['form'] = DataRequestForm
        return super().get_form(request, obj, **kwargs)

    def get_readonly_fields(self, request, obj=None):
        if obj: # Editing existing
            return ('user', 'request_type', 'description', 'created_at', 'updated_at', 'processed_at', 'processed_by')
        # For new, user and description are editable. Response and status are for admin.
        return ('created_at', 'updated_at', 'processed_at', 'processed_by', 'status', 'response')

    def save_model(self, request, obj, form, change):
        if change and 'status' in form.cleaned_data:
            original_obj = self.model.objects.filter(pk=obj.pk).first()
            
            current_status_is_pending = not original_obj or original_obj.status == obj._meta.get_field('status').default # 'pending'
            new_status_is_not_pending = form.cleaned_data['status'] != obj._meta.get_field('status').default

            if current_status_is_pending and new_status_is_not_pending and not obj.processed_by:
                obj.processed_by = request.user
            
            if new_status_is_not_pending:
                obj.processed_at = timezone.now()
            else: # Status is 'pending' or reverted to 'pending'
                obj.processed_by = None
                obj.processed_at = None
        super().save_model(request, obj, form, change)

# --- Customization Settings ---
@admin.register(SiteCustomization)
class SiteCustomizationAdmin(SingletonModelAdmin):
    form = SiteCustomizationForm
    # Note: SiteSettings model handles maintenance_mode and google_analytics_id
    # SiteCustomizationForm might still include them; if so, they'll appear.
    # For a cleaner UI, ensure SiteCustomizationForm excludes fields managed by SiteSettings.
    # Assuming SiteCustomizationForm is correctly defined in forms_customization.py
    fieldsets = (
        ('Identificação do Site', {'fields': ('site_name', 'site_slogan')}),
        ('Logos e Favicon', {'fields': ('logo', 'logo_dark', 'logo_footer', 'favicon')}),
        ('Cores do Tema', {'fields': ('primary_color', 'secondary_color', 'success_color', 'danger_color', 'warning_color', 'info_color')}),
        ('Tipografia', {'fields': ('font_family', 'font_size_base')}),
        ('Layout', {'fields': ('header_style', 'footer_style')}),
        ('Recursos', {'fields': ('dark_mode', 'rtl_support', 'maintenance_mode', 'maintenance_message')}), # maintenance_mode is also in SiteSettings
        ('Redes Sociais', {'fields': ('facebook_url', 'twitter_url', 'instagram_url', 'linkedin_url', 'youtube_url')}),
        ('Informações de Contato', {'fields': ('contact_email', 'contact_phone', 'contact_address')}), # contact_email is also in SiteSettings
        ('SEO e Análise (IDs)', {'fields': ('google_analytics_id', 'google_tag_manager_id', 'facebook_pixel_id')}), # google_analytics_id is also in SiteSettings
        ('Scripts e CSS Personalizados (Global)', {'fields': ('header_scripts', 'footer_scripts', 'custom_css')}),
    )
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CustomCSS)
class CustomCSSAdmin(admin.ModelAdmin):
    form = CustomCSSForm
    list_display = ('name', 'slug', 'is_active', 'updated_at')
    list_filter = ('is_active',)
    search_fields = ('name', 'slug', 'css')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

@admin.register(CustomJavaScript)
class CustomJavaScriptAdmin(admin.ModelAdmin):
    form = CustomJavaScriptForm
    list_display = ('name', 'slug', 'location', 'is_active', 'updated_at')
    list_filter = ('is_active', 'location')
    search_fields = ('name', 'slug', 'script')
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ('created_at', 'updated_at')

