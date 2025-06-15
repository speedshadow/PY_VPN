from django.shortcuts import render, get_object_or_404, redirect
from .models import VPN
from analytics.models import Analytics

def home(request):
    vpns_homepage = VPN.objects.filter(show_on_homepage=True).order_by('-overall_rating')[:3]
    all_devices = [
        "android", "ios", "mac", "linux", "windows",
        "router", "smarttv", "firestick", "other"
    ]
    # Passa a posição para badges (1,2,3)
    vpns_with_rank = [(vpn, idx+1) for idx, vpn in enumerate(vpns_homepage)]
    return render(request, 'home.html', {'vpns_homepage': vpns_homepage, 'all_devices': all_devices, 'vpns_with_rank': vpns_with_rank})

# Lista pública de VPNs (homepage ou /vpn/)
def vpn_public_list(request):
    vpns = VPN.objects.filter(show_on_homepage=True)
    all_devices = [
        "android", "ios", "mac", "linux", "windows",
        "router", "smarttv", "firestick", "other"
    ]
    return render(request, 'vpn/vpn_list_public.html', {'vpns': vpns, 'all_devices': all_devices})

# Detalhe público de VPN

def vpn_public_detail(request, slug):
    # TODO: Enforce unique slugs at the model/admin level
    vpns = VPN.objects.filter(slug=slug)
    if not vpns.exists():
        from django.http import Http404
        raise Http404("VPN not found.")
    vpn = vpns.first()  # Pick the first if multiple found

    return render(request, 'vpn/vpn_detail_public.html', {'vpn': vpn})

# Affiliate click tracking view
from django.http import HttpResponseBadRequest

def vpn_affiliate_click(request, pk):
    vpn = get_object_or_404(VPN, pk=pk)
    if not vpn.affiliate_link:
        return HttpResponseBadRequest("No affiliate link available.")
    # Log the click
    Analytics.objects.create(
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
        is_bot=False,
        page_url=request.path,
        referrer=request.META.get('HTTP_REFERER', ''),
        event_type='affiliate_click',
    )
    return redirect(vpn.affiliate_link)
