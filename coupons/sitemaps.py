from django.contrib.sitemaps import Sitemap
from django.urls import reverse
from .models import Coupon

class CouponSitemap(Sitemap):
    changefreq = "daily"
    priority = 0.8
    protocol = 'https'

    def items(self):
        # Retorna apenas cupons ativos
        return Coupon.objects.filter(is_active=True)
    
    def lastmod(self, obj):
        return obj.updated_at
    
    def location(self, obj):
        # Retorna a URL do cupom, se houver link de produto
        if obj.product_link:
            return obj.product_link
        # Se não houver link de produto, retorna a URL da lista de cupons
        return reverse('coupons:coupon_public_list')
