from django.urls import path

from chat.consumers import ChatConsumer, ChatAPIConsumer


websocket_urlpatterns = [
    path('ws/chat/<int:chat_id>/', ChatConsumer.as_asgi()),
    path('ws/chat_api/<str:url_name>/<int:chat_id>/', ChatAPIConsumer.as_asgi()),
]
