from django.urls import path
from .views import blogpost_list, blogpost_create, blogpost_edit, blogpost_delete
from .views_faq import faq_view

urlpatterns = [
    path('', blogpost_list, name='blogpost_list'),
    path('create/', blogpost_create, name='blogpost_create'),
    path('edit/<int:post_id>/', blogpost_edit, name='blogpost_edit'),
    path('delete/<int:post_id>/', blogpost_delete, name='blogpost_delete'),
    path('faq/', faq_view, name='faq'),
]
