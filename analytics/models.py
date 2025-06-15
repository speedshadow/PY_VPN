from django.db import models

class Analytics(models.Model):
    EVENT_CHOICES = [
        ("visit", "Visit"),
        ("affiliate_click", "Affiliate Click"),
        ("bot", "Bot Visit"),
    ]
    ip_address = models.GenericIPAddressField()
    user_agent = models.TextField()
    is_bot = models.BooleanField(default=False)
    page_url = models.CharField(max_length=255)
    referrer = models.CharField(max_length=255, blank=True, null=True)
    event_type = models.CharField(max_length=32, choices=EVENT_CHOICES)
    timestamp = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.event_type} - {self.ip_address} @ {self.timestamp}"

    @classmethod
    def visits_today(cls):
        from django.utils import timezone
        now = timezone.now()
        return cls.objects.filter(timestamp__date=now.date(), is_bot=False, event_type="visit").count()

    @classmethod
    def visits_week(cls):
        from django.utils import timezone
        now = timezone.now()
        week_ago = now - timezone.timedelta(days=7)
        return cls.objects.filter(timestamp__gte=week_ago, is_bot=False, event_type="visit").count()

    @classmethod
    def visits_month(cls):
        from django.utils import timezone
        now = timezone.now()
        month_ago = now - timezone.timedelta(days=30)
        return cls.objects.filter(timestamp__gte=month_ago, is_bot=False, event_type="visit").count()

    @classmethod
    def last_5min_visitors(cls):
        from django.utils import timezone
        now = timezone.now()
        five_min_ago = now - timezone.timedelta(minutes=5)
        return cls.objects.filter(timestamp__gte=five_min_ago, is_bot=False, event_type="visit").count()

    @classmethod
    def bots_online(cls):
        from django.utils import timezone
        now = timezone.now()
        five_min_ago = now - timezone.timedelta(minutes=5)
        return cls.objects.filter(timestamp__gte=five_min_ago, is_bot=True).count()
