from rest_framework import serializers
from rest_framework.fields import empty

from common.utils import CustomSerializer

from chats.models import RoomChat, PrivateChat, Message

from users.models import User


class MessageSerializer(serializers.ModelSerializer):
    user = serializers.ReadOnlyField(source='user.username')

    class Meta:
        model = Message
        exclude = ['content_type', 'object_id']


class BaseChatSerializer(CustomSerializer, serializers.ModelSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        context = kwargs.pop('context', {})
        self.user_id = context['user_id']
        super().__init__(instance, data, **kwargs)


class UserSlugField(serializers.SlugRelatedField):
    """Field for limited choices."""

    def get_queryset(self):
        if hasattr(self.root, 'user_id'):
            query = User.objects.filter(
                followers__from_user=self.root.user_id,
            )
            return query


class RoomChatSerializer(BaseChatSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    users = UserSlugField(slug_field='username', many=True)

    class Meta:
        model = RoomChat
        fields = [
            'id',
            'owner',
            'created',
            'users',
            'name',
            'image',
        ]


class PrivateChatSerializer(BaseChatSerializer):
    user = UserSlugField(slug_field='username', source='second_user')

    class Meta:
        model = PrivateChat
        fields = ['id', 'user']


class RoomChatsSerializer(RoomChatSerializer):
    last_message = serializers.SerializerMethodField()

    def get_last_message(self, instance):
        data = {
            'user': instance.last_message_user,
            'date': instance.last_message_time,
            'text': instance.last_message,
        }
        return data

    class Meta:
        model = RoomChat
        fields = RoomChatSerializer.Meta.fields + ['last_message']


class PrivateChatsSerializer(PrivateChatSerializer):
    last_message = serializers.SerializerMethodField()

    def get_last_message(self, instance):
        data = {
            'user': instance.last_message_user,
            'date': instance.last_message_time,
            'text': instance.last_message,
        }
        return data

    class Meta:
        model = PrivateChat
        fields = PrivateChatSerializer.Meta.fields + ['last_message']
