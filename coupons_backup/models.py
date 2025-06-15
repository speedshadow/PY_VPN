from django.db import models

class Coupon(models.Model):
    product_name = models.CharField(max_length=120)
    product_link = models.URLField(blank=True, null=True)
    coupon_code = models.CharField(max_length=50, blank=True, null=True)
    direct_link = models.URLField(blank=True, null=True)
    has_expiry = models.BooleanField(default=False)
    expiry_date = models.DateTimeField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.product_name
