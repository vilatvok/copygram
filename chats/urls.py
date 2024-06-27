from django.urls import path

from chats.views import rooms, private


app_name = 'chats'


urlpatterns = [
    path('rooms/', rooms.RoomChatsView.as_view(), name='rooms'),
    path('private-chats/', private.PrivateChatsView.as_view(), name='chats'),
    path(
        route='create-room/',
        view=rooms.CreateRoomView.as_view(),
        name='create_room',
    ),
    path(
        route='rooms/<int:chat_id>/',
        view=rooms.RoomChatView.as_view(),
        name='room_chat',
    ),
    path(
        route='rooms/<int:room_id>/members/',
        view=rooms.RoomUsersView.as_view(),
        name='room_users',
    ),
    path(
        route='rooms/<int:room_id>/edit-room/',
        view=rooms.EditRoomView.as_view(),
        name='edit_room',
    ),
    path(
        route='rooms/<int:room_id>/delete-room/',
        view=rooms.DeleteRoomView.as_view(),
        name='delete_room',
    ),
    path(
        route='private-chats/<int:chat_id>/',
        view=private.PrivateChatView.as_view(),
        name='private_chat',
    ),
    path(
        route='create-chat/<slug:user_slug>/',
        view=private.CreatePrivateChatView.as_view(),
        name='create_chat',
    ),
]
