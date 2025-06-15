from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from vpn.models import VPN
from categories.models import Category
from coupons.models import Coupon
from analytics.models import Analytics
from django.db.models import Count
from django.utils import timezone
from django.db.models.functions import TruncDate
import json
from .forms import VPNForm

@login_required(login_url='/admin/login/')
def dashboard(request):
    from custompages.models import CustomPage
    
    stats = {
        'total_vpns': VPN.objects.count(),
        'total_categories': Category.objects.count(),
        'total_coupons': Coupon.objects.count(),
        'visitors_5min': Analytics.last_5min_visitors(),
        'visits_today': Analytics.visits_today(),
        'visits_week': Analytics.visits_week(),
        'visits_month': Analytics.visits_month(),
        'bots_online': Analytics.bots_online(),
        'total_custom_pages': CustomPage.objects.count(),
    }

    # --- Visits last 7 days (non-bot) ---
    seven_days_ago = timezone.now() - timezone.timedelta(days=6)
    visits_qs = (
        Analytics.objects.filter(
            timestamp__date__gte=seven_days_ago.date(),
            is_bot=False,
            event_type="visit",
        )
        .annotate(day=TruncDate("timestamp"))
        .values("day")
        .order_by("day")
        .annotate(total=Count("id"))
    )
    visits_dict = {item["day"].isoformat(): item["total"] for item in visits_qs}
    labels_visits = [
        (seven_days_ago + timezone.timedelta(days=i)).date().isoformat() for i in range(7)
    ]
    visits_dataset = [visits_dict.get(d, 0) for d in labels_visits]
    visits_chart_data = json.dumps(
        {
            "labels": labels_visits,
            "datasets": [
                {
                    "label": "Visits",
                    "data": visits_dataset,
                    "backgroundColor": "rgba(99, 102, 241, 0.2)",
                    "borderColor": "rgba(99, 102, 241, 1)",
                    "borderWidth": 2,
                    "tension": 0.4,
                }
            ],
        }
    )

    # --- Bots distribution (last 7 days) ---
    bots_map = {
        "Google": ["google", "googlebot"],
        "Bing": ["bing", "bingbot"],
        "Yahoo": ["yahoo"],
        "Yandex": ["yandex"],
    }
    bots_counts = {}
    for label, substr in bots_map.items():
        bots_counts[label] = Analytics.objects.filter(
            is_bot=True,
            timestamp__gte=seven_days_ago,
            user_agent__iregex="|".join(substr),
        ).count()

    bots_chart_data = json.dumps(
        {
            "labels": list(bots_counts.keys()),
            "datasets": [
                {
                    "label": "Bots",
                    "data": list(bots_counts.values()),
                    "backgroundColor": [
                        "rgba(16, 185, 129, 0.8)",
                        "rgba(59, 130, 246, 0.8)",
                        "rgba(245, 158, 11, 0.8)",
                        "rgba(239, 68, 68, 0.8)",
                    ],
                }
            ],
        }
    )

    # --- Affiliate clicks (last 30 days) ---
    aff_qs = (
        Analytics.objects.filter(
            event_type="affiliate_click",
            timestamp__gte=timezone.now() - timezone.timedelta(days=30),
        )
        .values("page_url")
        .annotate(total=Count("id"))
        .order_by("-total")[:6]
    )
    aff_labels = [item["page_url"] for item in aff_qs]
    aff_counts = [item["total"] for item in aff_qs]
    aff_clicks_chart_data = json.dumps(
        {
            "labels": aff_labels,
            "datasets": [
                {
                    "label": "Affiliate Clicks",
                    "data": aff_counts,
                    "backgroundColor": "rgba(168, 85, 247, 0.7)",
                }
            ],
        }
    )

    context = {
        "stats": stats,
        "visits_chart_data": visits_chart_data,
        "bots_chart_data": bots_chart_data,
        "aff_clicks_chart_data": aff_clicks_chart_data,
    }
    return render(request, "dashboard/dashboard.html", context)

@login_required(login_url='/admin/login/')
def vpn_list(request):
    vpns = VPN.objects.all()
    return render(request, 'dashboard/vpn_list.html', {'vpns': vpns})

@login_required(login_url='/admin/login/')
def vpn_create(request):
    if request.method == 'POST':
        form = VPNForm(request.POST, request.FILES)
        if form.is_valid():
            form.save()
            return redirect('vpn_list')
    else:
        form = VPNForm()
    return render(request, 'dashboard/vpn_form.html', {'form': form, 'vpn': None})

@login_required(login_url='/admin/login/')
def vpn_edit(request, vpn_id):
    vpn = get_object_or_404(VPN, pk=vpn_id)
    if request.method == 'POST':
        form = VPNForm(request.POST, request.FILES, instance=vpn)
        if form.is_valid():
            print("DEBUG vpn_edit cleaned_data:", form.cleaned_data)
            saved_obj = form.save()
            print("DEBUG vpn_edit saved id:", saved_obj.id)
            return redirect('vpn_list')
        else:
            print("DEBUG vpn_edit form errors:", form.errors.as_json())
    else:
        form = VPNForm(instance=vpn)
    return render(request, 'dashboard/vpn_form.html', {'form': form, 'vpn': vpn})

@login_required(login_url='/admin/login/')
def vpn_delete(request, vpn_id):
    vpn = get_object_or_404(VPN, pk=vpn_id)
    if request.method == 'POST':
        vpn.delete()
        return redirect('vpn_list')
    return render(request, 'dashboard/vpn_confirm_delete.html', {'vpn': vpn})
