from django.urls import path
from .views_public import coupon_public_list

app_name = 'coupons_public'

urlpatterns = [
    path('', coupon_public_list, name='coupon_public_list'),
    # Removidas as rotas de detalhe e redirecionamento
]
