from django.urls import path

from chats.views import templates


app_name = 'chats'


urlpatterns = [
    path('rooms/', templates.RoomChatsView.as_view(), name='rooms'),
    path('private-chats/', templates.PrivateChatsView.as_view(), name='chats'),
    path(
        route='create-room/',
        view=templates.CreateRoomView.as_view(),
        name='create_room',
    ),
    path(
        route='rooms/<int:chat_id>/',
        view=templates.RoomChatView.as_view(),
        name='room_chat',
    ),
    path(
        route='rooms/<int:room_id>/members/',
        view=templates.RoomUsersView.as_view(),
        name='room_users',
    ),
    path(
        route='rooms/<int:room_id>/edit-room/',
        view=templates.EditRoomView.as_view(),
        name='edit_room',
    ),
    path(
        route='rooms/<int:room_id>/delete-room/',
        view=templates.DeleteRoomView.as_view(),
        name='delete_room',
    ),
    path(
        route='private-chats/<int:chat_id>/',
        view=templates.PrivateChatView.as_view(),
        name='private_chat',
    ),
    path(
        route='create-chat/<slug:user_slug>/',
        view=templates.CreatePrivateChatView.as_view(),
        name='create_chat',
    ),
]
