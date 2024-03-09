from django.db.models import Q

from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from chat.permissions.api import IsRoomOwner, IsPrivateMember
from chat.models import RoomChat, PrivateChat
from chat.serializers import MessageSerializer, RoomChatSerializer, PrivateChatSerializer


class RoomChatViewSet(ModelViewSet):
    serializer_class = RoomChatSerializer
    permission_classes = [IsAuthenticated, IsRoomOwner]

    def get_queryset(self):
        return (
            RoomChat.objects.filter(users__in=[self.request.user]).
            select_related('owner')
        )
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_id'] = self.request.user.id
        return context
    
    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, fields=['id', 'owner']
        )
        messages = (
            instance.messages.all().
            select_related('user', 'content_type').prefetch_related('files')
        )
        messages_serializer = MessageSerializer(messages, many=True)
        result = {**serializer.data, 'messages': messages_serializer.data}
        return Response(result)
    

class PrivateChatViewSet(
    mixins.ListModelMixin,
    mixins.RetrieveModelMixin,
    mixins.CreateModelMixin,
    mixins.DestroyModelMixin,
    GenericViewSet
):
    serializer_class = PrivateChatSerializer
    permission_classes = [IsAuthenticated, IsPrivateMember]

    def get_queryset(self):
        return PrivateChat.objects.filter(
            Q(first_user=self.request.user) | Q(second_user=self.request.user)
        ).select_related('first_user', 'second_user')
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_id'] = self.request.user.id
        return context
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, fields=['id'])
        messages = (
            instance.messages.all().
            select_related('user', 'content_type').prefetch_related('files')
        )
        messages_serializer = MessageSerializer(messages, many=True)
        result = {**serializer.data, 'messages': messages_serializer.data}
        return Response(result)