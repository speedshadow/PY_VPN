from django.urls import path
from .views_public import category_public_detail

urlpatterns = [
    path('<slug:slug>/', category_public_detail, name='category_public_detail'),
]
