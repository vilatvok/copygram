from django.db.models import Q

from rest_framework import mixins
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from rest_framework.viewsets import ModelViewSet, GenericViewSet

from chat.permissions import IsRoomOwner, IsPrivateMember
from chat.models import RoomChat, PrivateChat
from chat.serializers import RoomChatSerializer, PrivateChatSerializer


class RoomChatViewSet(ModelViewSet):
    serializer_class = RoomChatSerializer
    permission_classes = [IsAuthenticated, IsRoomOwner]

    def get_queryset(self):
        return RoomChat.objects.filter(users__in=[self.request.user])
    
    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_id'] = self.request.user.id
        return context
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=self.request.user)
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(
            instance, fields=('id', 'owner', 'users')
        )
        return Response(serializer.data)
    

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
    
    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data)
    
    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, fields=('id', 'user'))
        return Response(serializer.data)