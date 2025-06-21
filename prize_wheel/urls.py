from django.urls import path
from . import views

app_name = 'prize_wheel'

urlpatterns = [
    path('api/spin/', views.spin_the_wheel_api, name='api_spin_the_wheel'),
    path('api/submit-email/<int:attempt_id>/', views.submit_winner_email_api, name='api_submit_winner_email'),
]
