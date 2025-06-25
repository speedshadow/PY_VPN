from django.contrib import admin
from .models import PrizeWheelConfig, Prize, SpinAttempt

@admin.register(PrizeWheelConfig)
class PrizeWheelConfigAdmin(admin.ModelAdmin):
    list_display = ('__str__', 'is_active', 'attempts_per_ip_daily', 'overall_win_chance')
    # Since we expect only one instance, consider using django-solo or similar
    # or provide guidance to only create/edit the existing one.
    def has_add_permission(self, request):
        # Allow adding if no instance exists yet
        return not PrizeWheelConfig.objects.exists()

@admin.register(Prize)
class PrizeAdmin(admin.ModelAdmin):
    list_display = ('name', 'probability_weight', 'is_active', 'quantity')
    list_filter = ('is_active',)
    search_fields = ('name', 'description')
    ordering = ('-probability_weight', 'name')

@admin.register(SpinAttempt)
class SpinAttemptAdmin(admin.ModelAdmin):
    list_display = ('timestamp', 'ip_address', 'prize_won', 'winner_email', 'has_submitted_email')
    list_filter = ('timestamp', 'prize_won', 'winner_email') # Added winner_email for filtering (IsEmptyListFilter could be even better)
    search_fields = ('ip_address', 'prize_won__name', 'winner_email')
    readonly_fields = ('ip_address', 'prize_won', 'winner_email', 'timestamp')
    date_hierarchy = 'timestamp'
    ordering = ('-timestamp',)

    def has_submitted_email(self, obj):
        return bool(obj.winner_email)
    has_submitted_email.boolean = True
    has_submitted_email.short_description = 'Email Submitted?'

    def has_add_permission(self, request):
        # Users should not be able to add spin attempts manually via admin
        return False

    def has_change_permission(self, request, obj=None):
        # Prevent changing existing spin attempts
        return False

    # For a more advanced filter of "Winners" vs "Non-Winners",
    # we could create a custom SimpleListFilter.
    # For now, filtering by 'winner_email' (empty/not empty) and 'prize_won' (empty/not empty) should help.
