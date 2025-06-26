"""
URL configuration for core project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/5.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path
from django.views.generic import TemplateView
from django.contrib.sitemaps.views import sitemap
from core.sitemaps import StaticViewSitemap, VPNSitemap, CategorySitemap, BlogSitemap, CustomPageSitemap, ManualXMLSitemap

from custompages.views import public_custompage

from django.urls import include
from django.conf import settings
from django.conf.urls.static import static

from categories import urls_public as categories_public_urls
from blog import urls_public as blog_public_urls
from coupons import urls_public as coupons_public_urls
from vpn import urls as vpn_urls

from vpn.views import vpn_home_view
from blog.views_faq import faq_view

urlpatterns = [
    # Admin and system URLs
    path('accounts/', include('django.contrib.auth.urls')),
    path('admin/', admin.site.urls),
    path('sitemap.xml', sitemap, {'sitemaps': {
        'static': StaticViewSitemap,
        'vpns': VPNSitemap,
        'categories': CategorySitemap,
        'blog': BlogSitemap,
        'custompages': CustomPageSitemap,
        'manual_xml': ManualXMLSitemap,
    }}, name='sitemap'),
    path('ckeditor5/', include('django_ckeditor_5.urls'), name='ck_editor_5_upload_file'),
    path('robots.txt', TemplateView.as_view(template_name='robots.txt', content_type='text/plain'), name='robots'),

    # App URLs
    path('', vpn_home_view, name='home'),
    path('vpn/', include(vpn_urls)),
    path('categories/', include(categories_public_urls)),
    path('blog/', include(blog_public_urls)),
    path('coupons/', include(coupons_public_urls)),
    path('contact/', include('contact.urls')),
    path('prize-wheel/', include('prize_wheel.urls', namespace='prize_wheel')),

    # FAQ explicit URL
    path('faq/', faq_view, name='faq'),

    # Slug-based URLs (should be last)
    path('best-vpns-for-<slug:slug>/', categories_public_urls.category_public_detail, name='category_public_detail'),
    path('<slug:slug>/', public_custompage, name='public_custompage'),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
