from django.urls import path
from . import views

urlpatterns = [
    path('', views.custompage_list, name='custompage_list'),
    path('create/', views.custompage_create, name='custompage_create'),
    path('edit/<int:pk>/', views.custompage_edit, name='custompage_edit'),
    path('delete/<int:pk>/', views.custompage_delete, name='custompage_delete'),
]
