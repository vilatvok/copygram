from rest_framework import serializers
from rest_framework.fields import empty

from django.contrib.auth import get_user_model

from common.utils import set_serializer_fields

from chat.models import RoomChat, PrivateChat, Message


User = get_user_model()


class MessageSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Message
        exclude = ['content_type', 'object_id']


class BaseChatSerializer(serializers.ModelSerializer):
    messages = MessageSerializer(many=True, read_only=True)

    def __init__(self, instance=None, data=empty, **kwargs):
        fields = kwargs.pop('fields', None)
        context = kwargs.pop('context', {})
        self.user_id = context['user_id']
        super().__init__(instance, data, **kwargs)
        
        if fields:
            set_serializer_fields(fields, self.fields)


class UserSlugField(serializers.SlugRelatedField):
    """Field for limit choices."""

    def get_queryset(self):
        if hasattr(self.root, 'user_id'):
            query = User.objects.filter(
                user_to__user_from=self.root.user_id
            )
            return query


class RoomChatSerializer(BaseChatSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    users = UserSlugField(slug_field='username', many=True)

    class Meta:
        model = RoomChat
        fields = '__all__'


class PrivateChatSerializer(BaseChatSerializer):
    user = UserSlugField(slug_field='username', source='second_user')

    class Meta:
        model = PrivateChat
        fields = ['id', 'user', 'messages']