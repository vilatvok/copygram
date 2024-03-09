from django.urls import path

from chat.views import templates


app_name = 'chat'

urlpatterns = [
    path('chats/', templates.PrivateChatsView.as_view(), name='chats'),
    path('rooms/', templates.RoomChatsView.as_view(), name='rooms'),
    path('create_chat/<slug:user_slug>/', templates.create_private_chat, name='create_chat'),
    path('private/<int:chat_id>/', templates.PrivateChatView.as_view(), name='private_chat'),
    path('room/<int:chat_id>/', templates.RoomChatView.as_view(), name='room_chat'),
    path('room/<int:room_id>/members/', templates.RoomUsersView.as_view(), name='room_users'),
    path('create_room/', templates.CreateRoomView.as_view(), name='create_room'),
    path('edit_room/<int:room_id>/', templates.EditRoomView.as_view(), name='edit_room'),
    path('delete_room/<int:room_id>/', templates.DeleteRoomView.as_view(), name='delete_room'),
]