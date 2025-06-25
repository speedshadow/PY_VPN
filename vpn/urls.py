from django.urls import path
from . import views
from .views import vpn_public_list, vpn_public_detail, vpn_affiliate_click, vpn_test_view

urlpatterns = [
    path('compare/', views.compare_vpns_view, name='compare_vpns'),
    path('', vpn_public_list, name='vpn_public_list'),
    path('affiliate/<int:pk>/', vpn_affiliate_click, name='vpn_affiliate_click'),
    path('<slug:slug>/', vpn_public_detail, name='vpn_public_detail'),
    path('test/', vpn_test_view, name='vpn_test_view'),
]
