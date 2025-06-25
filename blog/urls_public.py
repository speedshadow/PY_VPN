from django.urls import path
from .views_public import blog_public_list, blog_public_detail, blog_like, blog_category_list

urlpatterns = [
    path('', blog_public_list, name='blog_public_list'),
    path('categoria/<slug:slug>/', blog_category_list, name='blog_category_list'),
    path('<slug:slug>/', blog_public_detail, name='blog_public_detail'),
    path('<slug:slug>/like/', blog_like, name='blog_like'),
]
