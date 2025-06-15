from django.urls import path
from .views import category_list, category_create, category_edit, category_delete

urlpatterns = [
    path('', category_list, name='category_list'),
    path('create/', category_create, name='category_create'),
    path('edit/<int:category_id>/', category_edit, name='category_edit'),
    path('delete/<int:category_id>/', category_delete, name='category_delete'),
]
