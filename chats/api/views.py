from django.db.models import Q

from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet

from common.utils import NonUpdateViewSet

from chats.mixins import ChatAPIMixin
from chats.permissions import IsRoomOwner, IsPrivateMember
from chats.models import RoomChat, PrivateChat
from chats.api.serializers import (
    PrivateChatSerializer,
    PrivateChatsSerializer,
    RoomChatSerializer,
    RoomChatsSerializer,
)


class RoomChatViewSet(ChatAPIMixin, ModelViewSet):
    permission_classes = [IsAuthenticated, IsRoomOwner]

    def get_queryset(self):
        rooms = (
            RoomChat.objects.annotated().
            filter(users__in=[self.request.user]).
            select_related('owner').prefetch_related('users')
        )
        return rooms

    def get_serializer_class(self):
        if self.action == 'list':
            return RoomChatsSerializer
        return RoomChatSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)


class PrivateChatViewSet(ChatAPIMixin, NonUpdateViewSet):
    permission_classes = [IsAuthenticated, IsPrivateMember]

    def get_queryset(self):
        user = self.request.user
        chats = PrivateChat.objects.annotated().filter(
            Q(first_user=user) |
            Q(second_user=user),
        ).select_related('first_user', 'second_user')
        return chats

    def get_serializer_class(self):
        if self.action == 'list':
            return PrivateChatsSerializer
        return PrivateChatSerializer
