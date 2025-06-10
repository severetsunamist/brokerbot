from django.urls import path
from .views import webhook, start_bot

urlpatterns = [
    path('webhook/', webhook, name='bot_webhook'),
]

# Start the bot when Django starts (for development)
start_bot()