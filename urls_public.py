from django.urls import path
from .views_public import faq_view, contact_view

urlpatterns = [
    path('faq/', faq_view, name='faq'),
    path('contact/', contact_view, name='contact'),
]
