from django.urls import path
from django.views.generic import RedirectView
from . import views

app_name = 'coupons'

urlpatterns = [
    # Lista de cupons
    path('', views.coupon_list, name='list'),
    
    # CRUD de cupons
    path('novo/', views.coupon_create, name='create'),
    path('editar/<int:pk>/', views.coupon_edit, name='edit'),
    path('excluir/<int:pk>/', views.coupon_delete, name='delete'),
    path('toggle-status/<int:pk>/', views.toggle_coupon_status, name='toggle_status'),
    
    # Redirecionamentos para compatibilidade reversa
    path('create/', RedirectView.as_view(pattern_name='coupons:create', permanent=False)),
    path('edit/<int:pk>/', RedirectView.as_view(pattern_name='coupons:edit', permanent=False)),
    path('delete/<int:pk>/', RedirectView.as_view(pattern_name='coupons:delete', permanent=False)),
]
