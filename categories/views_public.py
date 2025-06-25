from django.shortcuts import render, get_object_or_404
from .models import Category
from vpn.models import VPN

# Lista todas as categorias


# Página de uma categoria e VPNs relacionadas

def category_public_detail(request, slug):
    from vpn.models import VPN
    category = get_object_or_404(Category, slug=slug)
    vpns = category.vpns.all()
    # Lista de devices igual homepage
    all_devices = [
        "android", "ios", "mac", "linux", "windows", "router", "smarttv", "firestick", "other"
    ]
    return render(request, 'categories/category_detail_public.html', {
        'category': category,
        'vpns': vpns,
        'all_devices': all_devices,
    })
