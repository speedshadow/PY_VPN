from django.urls import path, include
from . import views as general_views
from . import views_https

from . import views_seo
from . import views_compliance
from . import views_customization

app_name = 'settings'

# General and HTTPS settings
urlpatterns = [
    path('', general_views.settings_edit, name='settings_edit'),
    path('https-setup/', views_https.https_setup_wizard, name='https_setup_wizard'),
]



# SEO URLs
seo_urlpatterns = [
    path('', views_seo.seo_dashboard, name='seo_dashboard'),
    path('settings/', views_seo.seo_settings_edit, name='seo_settings_edit'),
    path('pages/', views_seo.page_seo_list, name='page_seo_list'),
    path('pages/add/', views_seo.page_seo_edit, name='page_seo_add'),
    path('pages/<int:pk>/edit/', views_seo.page_seo_edit, name='page_seo_edit'),
    path('pages/<int:pk>/delete/', views_seo.page_seo_delete, name='page_seo_delete'),
    path('sitemap/', views_seo.sitemap_list, name='sitemap_list'),
    path('sitemap/add/', views_seo.sitemap_add, name='sitemap_add'),
    path('sitemap/<int:pk>/edit/', views_seo.sitemap_edit, name='sitemap_edit'),
    path('sitemap/<int:pk>/delete/', views_seo.sitemap_delete, name='sitemap_delete'),
    path('sitemap/generate/', views_seo.sitemap_generate, name='sitemap_generate'),
    path('sitemap/download/', views_seo.sitemap_download, name='sitemap_download_admin'), # Admin download
    path('analysis/', views_seo.seo_analysis, name='seo_analysis'),
    path('api/track/', views_seo.api_track_seo, name='api_track_seo'),
]

# Compliance URLs
compliance_urlpatterns = [
    path('', views_compliance.compliance_dashboard, name='compliance_dashboard'),
    path('settings/', views_compliance.compliance_settings, name='compliance_settings_edit'),
    path('data-requests/', views_compliance.data_requests, name='data_requests_list'),
    path('data-requests/<int:pk>/', views_compliance.data_request_detail, name='data_request_detail'),
    path('my-data-requests/', views_compliance.my_data_requests, name='my_data_requests'),
    path('my-data-requests/request/<str:request_type>/', views_compliance.request_my_data, name='request_my_data'),
    path('api/track-consent/', views_compliance.api_track_consent, name='api_track_consent'),
    path('api/data-request/', views_compliance.api_data_request, name='api_data_request_submit'),
]

# Customization URLs
customization_urlpatterns = [
    path('', views_customization.customization_dashboard, name='customization_dashboard'),
    path('general/', views_customization.customization_edit, name='customization_general_edit'),
    # path('theme-colors/', views_customization.theme_colors, name='theme_colors_edit'), # View was commented out
    # path('logo-favicon/', views_customization.logo_favicon_settings, name='logo_favicon_settings_edit'), # View was commented out
    # path('fonts/', views_customization.font_settings, name='font_settings_edit'), # View was commented out
    # path('social-media/', views_customization.social_media_links, name='social_media_links_list'), # View was commented out
    # path('social-media/add/', views_customization.social_media_link_add, name='social_media_link_add'), # View was commented out
    # path('social-media/<int:pk>/edit/', views_customization.social_media_link_edit, name='social_media_link_edit'), # View was commented out
    # path('social-media/<int:pk>/delete/', views_customization.social_media_link_delete, name='social_media_link_delete'), # View was commented out
    # path('contact-information/', views_customization.contact_information, name='contact_information_edit'), # View was commented out
    path('css/', views_customization.custom_css_list, name='custom_css_list'),
    path('css/add/', views_customization.custom_css_add, name='custom_css_add'),
    path('css/<int:pk>/edit/', views_customization.custom_css_edit, name='custom_css_edit'),
    path('css/<int:pk>/delete/', views_customization.custom_css_delete, name='custom_css_delete'),
    path('js/', views_customization.custom_js_list, name='custom_js_list'),
    path('js/add/', views_customization.custom_js_add, name='custom_js_add'),
    path('js/<int:pk>/edit/', views_customization.custom_js_edit, name='custom_js_edit'),
    path('js/<int:pk>/delete/', views_customization.custom_js_delete, name='custom_js_delete'),
    path('upload/logo/', views_customization.upload_logo, name='upload_logo'),
    path('upload/favicon/', views_customization.upload_favicon, name='upload_favicon'),
    path('upload/image/', views_customization.upload_image, name='upload_image_generic'), # For rich text editors etc.
    path('api/save/', views_customization.api_save_customization, name='api_save_customization'),
]

# Publicly accessible URLs (robots.txt, sitemap.xml, policy pages, etc.)
public_urlpatterns = [
    path('robots.txt', views_seo.robots_txt, name='robots_txt'),
    path('sitemap.xml', views_seo.sitemap_xml, name='sitemap_xml'),
    path('privacy-policy/', views_compliance.privacy_policy, name='privacy_policy'),
    path('terms-of-service/', views_compliance.terms_of_service, name='terms_of_service'),
    path('cookie-policy/', views_compliance.cookie_policy, name='cookie_policy'),
    path('cookie-settings/', views_compliance.cookie_settings, name='cookie_settings'),
    path('ccpa-opt-out/', views_compliance.ccpa_opt_out, name='ccpa_opt_out'),
    path('ccpa-opt-out/confirmation/', views_compliance.ccpa_opt_out_confirmation, name='ccpa_opt_out_confirmation'),
    path('custom.css', views_customization.custom_css, name='custom_css_file'),
    path('custom.js', views_customization.custom_js, name='custom_js_file'),
    path('theme.css', views_customization.theme_css, name='theme_css_file'),
]

# Combine all urlpatterns
urlpatterns += [

    path('seo/', include((seo_urlpatterns, 'seo'), namespace='seo')),
    path('compliance/', include((compliance_urlpatterns, 'compliance'), namespace='compliance')),
    path('customization/', include((customization_urlpatterns, 'customization'), namespace='customization')),
    # Public URLs are typically at the root or a common path, not under /dashboard/
    # These are added to the main urlpatterns directly or through the project's root urls.py
    # For now, adding them here for completeness within the app, but they might be moved.
] + public_urlpatterns

# Note: The 'public_urlpatterns' should ideally be included in the project's root urls.py
# or a dedicated 'public' app for better organization, especially if they are not prefixed
# by the 'settings' app's base path (e.g., /settings/robots.txt vs /robots.txt).
# For this example, they are included here and will be accessible under the app's path if
# this urls.py is included with a prefix like `path('settings/', include('settings.urls'))`
# in the main project urls.py. If included without a prefix, they will be root-level.
