from django.urls import path
from .views import coupon_list, coupon_create, coupon_edit, coupon_delete

urlpatterns = [
    path('', coupon_list, name='coupon_list'),
    path('create/', coupon_create, name='coupon_create'),
    path('edit/<int:coupon_id>/', coupon_edit, name='coupon_edit'),
    path('delete/<int:coupon_id>/', coupon_delete, name='coupon_delete'),
]
