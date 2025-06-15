from django.urls import path
from .views import vpn_public_list, vpn_public_detail, vpn_affiliate_click

urlpatterns = [
    path('', vpn_public_list, name='vpn_public_list'),
    path('affiliate/<int:pk>/', vpn_affiliate_click, name='vpn_affiliate_click'),
    path('<slug:slug>/', vpn_public_detail, name='vpn_public_detail'),
]
