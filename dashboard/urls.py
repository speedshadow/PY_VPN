from django.urls import path
from .views import dashboard, vpn_list, vpn_create, vpn_edit, vpn_delete

urlpatterns = [
    path('', dashboard, name='dashboard'),
    path('vpns/', vpn_list, name='vpn_list'),
    path('vpns/create/', vpn_create, name='vpn_create'),
    path('vpns/edit/<int:vpn_id>/', vpn_edit, name='vpn_edit'),
    path('vpns/delete/<int:vpn_id>/', vpn_delete, name='vpn_delete'),
]
