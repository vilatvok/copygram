from django.urls import path

from chats.consumers import ChatConsumer, ChatAPIConsumer


websocket_urlpatterns = [
    path('ws/chat/<int:chat_id>/', ChatConsumer.as_asgi()),
    path(
        route='ws/chat_api/<str:url_name>/<int:chat_id>/',
        view=ChatAPIConsumer.as_asgi(),
    ),
]
