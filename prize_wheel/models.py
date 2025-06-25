from django.db import models
from django.utils.translation import gettext_lazy as _

class PrizeWheelConfig(models.Model):
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Prize Wheel Active?"),
        help_text=_("Controls if the Prize Wheel feature is globally active.")
    )
    attempts_per_ip_daily = models.PositiveIntegerField(
        default=3,
        verbose_name=_("Attempts per IP (Daily)"),
        help_text=_("Maximum number of times a single IP can spin the wheel per day.")
    )
    overall_win_chance = models.DecimalField(
        default=0.5,
        max_digits=5,  # Allows for values like 99.999 or 0.001
        decimal_places=3, # Allows for precision like 0.5% (0.005)
        verbose_name=_("Overall Win Chance (%)"),
        help_text=_("The percentage probability of a user winning ANY prize on a spin. E.g., 0.5 for a 0.5% chance (1 in 200). Max 100.")
    )
    # Consider making this a singleton model in the admin or via a package like django-solo
    # For now, we'll assume only one instance of this model will be created/managed.

    def __str__(self):
        return str(_("Prize Wheel Settings"))

    class Meta:
        verbose_name = _("Prize Wheel Configuration")
        verbose_name_plural = _("Prize Wheel Settings")

class Prize(models.Model):
    name = models.CharField(
        max_length=255, 
        verbose_name=_("Prize Name")
    )
    description = models.TextField(
        blank=True, 
        verbose_name=_("Description")
    )
    probability_weight = models.PositiveIntegerField(
        default=1,
        verbose_name=_("Probability Weight"),
        help_text=_("A higher number increases the relative chance of winning this prize. E.g., a prize with a weight of 2 has twice the chance of one with a weight of 1.")
    )
    is_active = models.BooleanField(
        default=True,
        verbose_name=_("Prize Active?"),
        help_text=_("If unchecked, this prize cannot be won, even if the wheel is active.")
    )
    quantity = models.PositiveIntegerField(
        null=True, 
        blank=True, 
        verbose_name=_("Quantity Available"),
        help_text=_("Optional: Leave blank for unlimited quantity. If a number is set, it decreases each time it is won.")
    )

    def __str__(self):
        return self.name

    class Meta:
        verbose_name = _("Prize")
        verbose_name_plural = _("Prizes")
        ordering = ['-probability_weight', 'name']

class SpinAttempt(models.Model):
    ip_address = models.GenericIPAddressField(
        verbose_name=_("IP Address")
    )
    prize_won = models.ForeignKey(
        Prize, 
        null=True, 
        blank=True, 
        on_delete=models.SET_NULL, 
        verbose_name=_("Prize Won")
    )
    winner_email = models.EmailField(
        max_length=255,
        null=True, 
        blank=True, 
        verbose_name=_("Winner's Email"),
        help_text=_("Email collected if the user wins a prize.")
    )
    timestamp = models.DateTimeField(
        auto_now_add=True, 
        verbose_name=_("Attempt Date/Time")
    )

    def __str__(self):
        if self.prize_won:
            return f"{self.ip_address} won {self.prize_won.name} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"
        return f"Attempt from {self.ip_address} at {self.timestamp.strftime('%Y-%m-%d %H:%M')}"

    class Meta:
        verbose_name = _("Spin Attempt")
        verbose_name_plural = _("Spin Attempts")
        ordering = ['-timestamp']

