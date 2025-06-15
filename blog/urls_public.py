from django.urls import path
from .views_public import blog_public_list, blog_public_detail

urlpatterns = [
    path('', blog_public_list, name='blog_public_list'),
    path('<slug:slug>/', blog_public_detail, name='blog_public_detail'),
]
