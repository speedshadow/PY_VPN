from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from vpn.models import VPN
from categories.models import Category
from blog.models import BlogPost
from coupons.models import Coupon
from custompages.models import CustomPage

class StaticViewSitemap(Sitemap):
    priority = 1.0
    changefreq = 'daily'

    def items(self):
                                return ['home', 'coupons_public:coupon_public_list', 'blog_public_list']

    def location(self, item):
        return reverse(item)

class VPNSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.9
    def items(self):
        return VPN.objects.filter(is_active=True)
    def location(self, obj):
        return reverse('vpn_public_detail', kwargs={'slug': obj.slug})

class CategorySitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.7
    def items(self):
        return Category.objects.all()
    def location(self, obj):
        return reverse('category_public_detail', kwargs={'slug': obj.slug})

class BlogSitemap(Sitemap):
    changefreq = 'weekly'
    priority = 0.6
    def items(self):
                return BlogPost.objects.filter(published=True)
    def location(self, obj):
        return reverse('blog_public_detail', kwargs={'slug': obj.slug})

class CustomPageSitemap(Sitemap):
    changefreq = 'monthly'
    priority = 0.5
    def items(self):
        return CustomPage.objects.filter(is_active=True)
    def location(self, obj):
        return reverse('public_custompage', kwargs={'slug': obj.slug})
