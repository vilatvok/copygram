from django.urls import path

from users.consumers import UserStatusConsumer

websocket_urlpatterns = [
    path('ws/status/', UserStatusConsumer.as_asgi()),
]
