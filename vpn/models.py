from django.db import models
from django_ckeditor_5.fields import CKEditor5Field
from categories.models import Category

class VPN(models.Model):
    DEVICE_CHOICES = [
        ("android", "Android"),
        ("ios", "iOS"),
        ("mac", "Mac"),
        ("linux", "Linux"),
        ("windows", "Windows"),
        ("router", "Router"),
        ("smarttv", "Smart TV"),
        ("firestick", "Firestick"),
        ("other", "Other"),
    ]
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=120, blank=True)
    logo = models.URLField(blank=True, null=True)
    logo_upload = models.ImageField(upload_to='vpn_logos/', blank=True, null=True)
    categories = models.ManyToManyField(Category, related_name='vpns')
    devices_supported = models.JSONField(default=list)
    keep_logs = models.BooleanField(default=False)
    based_country = models.CharField(max_length=100)
    pros = models.TextField(blank=True, null=True)
    cons = models.TextField(blank=True, null=True)
    num_servers = models.PositiveIntegerField()
    price = models.CharField(max_length=50)
    affiliate_link = models.URLField(blank=True, null=True)
    show_on_homepage = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    # Ratings
    overall_rating = models.DecimalField(max_digits=3, decimal_places=1)
    security_rating = models.DecimalField(max_digits=3, decimal_places=1)
    privacy_rating = models.DecimalField(max_digits=3, decimal_places=1)
    speed_rating = models.DecimalField(max_digits=3, decimal_places=1)
    streaming_rating = models.DecimalField(max_digits=3, decimal_places=1)
    torrenting_rating = models.DecimalField(max_digits=3, decimal_places=1)
    additional_features_rating = models.DecimalField(max_digits=3, decimal_places=1)
    device_compatibility_rating = models.DecimalField(max_digits=3, decimal_places=1)
    server_locations_rating = models.DecimalField(max_digits=3, decimal_places=1)
    user_experience_rating = models.DecimalField(max_digits=3, decimal_places=1)
    # Speeds by country
    speeds_by_country = models.JSONField(default=dict, help_text="e.g. {'Germany': 300, 'Portugal': 430}")
    # Full review
    full_review = CKEditor5Field(blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def save(self, *args, **kwargs):
        # Auto-generate slug from name if empty
        if not self.slug:
            from django.utils.text import slugify
            base_slug = slugify(self.name)[:100]
            slug = base_slug
            counter = 1
            while VPN.objects.filter(slug=slug).exclude(pk=self.pk).exists():
                counter += 1
                slug = f"{base_slug}-{counter}"
            self.slug = slug
        super().save(*args, **kwargs)

    def get_pros_list(self):
        return [p.strip() for p in self.pros.splitlines() if p.strip()]

    def get_cons_list(self):
        return [c.strip() for c in self.cons.splitlines() if c.strip()]

    def __str__(self):
        return self.name


class VPNSpeed(models.Model):
    vpn = models.ForeignKey(VPN, related_name='country_speeds', on_delete=models.CASCADE)
    country = models.CharField(max_length=100, verbose_name="País")
    speed = models.CharField(max_length=50, verbose_name="Velocidade (Mbps)", help_text="Ex: 300 Mbps ou 'N/A'")

    class Meta:
        verbose_name = "Velocidade por País"
        verbose_name_plural = "Velocidades por País"
        unique_together = ('vpn', 'country') # Ensure only one speed entry per country for a given VPN

    def __str__(self):
        return f"{self.country}: {self.speed}"
