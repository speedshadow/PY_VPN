from django.urls import path
from .views_public import coupon_public_list

urlpatterns = [
    path('', coupon_public_list, name='coupon_public_list'),
]
