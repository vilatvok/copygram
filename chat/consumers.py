import base64
import json
import redis

from django.contrib.auth import get_user_model
from django.core.files.base import ContentFile

from channels.db import database_sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from rest_framework.serializers import Serializer

from djangochannelsrestframework.generics import GenericAsyncAPIConsumer
from djangochannelsrestframework.observer import model_observer
from djangochannelsrestframework.observer.generics import ObserverModelInstanceMixin, action

from chat.serializers import RoomChatSerializer, PrivateChatSerializer, MessageSerializer
from chat.models import Message, PrivateChat, RoomChat, MessageImages


User = get_user_model()
r = redis.Redis(host='redis', port=6379, db=0)


class ChatConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope['user']
        self.room = self.scope['url_route']['kwargs']['chat_id']
        self.room_name = f'chat_{self.room}'

        # Join room group
        await self.channel_layer.group_add(self.room_name, self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        await self.channel_layer.group_discard(self.room_name, self.channel_name)

    # Receive message from WebSocket
    async def receive(self, text_data):
        data = json.loads(text_data)
        chat = data['chat']
        action = data['action']
        
        if action == 'clear_messages':
            url = data['url']
            await self.clear_messages(url, chat)
            await self.channel_layer.group_send(
                self.room_name, 
                {
                    'type': 'chat.message', 
                    'action': action,
                    'chat': chat,
                    'url': url
                },
            )
        elif action == 'remove_chat':
            await self.remove_chat(chat)
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'chat.message',
                    'action': action,
                    'chat': chat
                }
            )
        
        elif action == 'leave_room':
            user = data['user']
            await self.leave_room(chat, user)
            await self.channel_layer.group_send(
                self.room_name,
                {
                    'type': 'chat.message', 
                    'action': action,
                    'chat': chat,
                    'user': user
                },
            )

        elif action == 'send_message':
            url = data['url']
            message = data['message']
            files = data.get('files', None)

            avatar = self.user.avatar.url if self.user.avatar else '/static/images/user.png'

            await self.save_message(url, chat, self.user.username, message, files)

            # Send message to room
            await self.channel_layer.group_send(
                self.room_name, 
                {
                    'type': 'chat.message', 
                    'action': action,
                    'url': url,
                    'chat': chat,
                    'user': self.user.username,
                    'avatar': avatar,
                    'message': message,
                    'files': files,
                },
            )

    # Receive message from room
    async def chat_message(self, event):
        # Send message to WebSocket
        await self.send(text_data=json.dumps(event))
        
    @database_sync_to_async
    def save_message(self, url, chat_id, user, message, files):
        user = User.objects.get(username=user)
        if url == 'room':
            chat = RoomChat.objects.get(id=chat_id)
            users = chat.users.exclude(username=user.username)
        else:
            chat = PrivateChat.objects.get(id=chat_id)
            users = chat.first_user if user == chat.first_user.username else chat.second_user

        if len(message):
            message_obj = Message.objects.create(
                user=user, 
                chat=chat,
                content=message
            )
        else:
            message_obj = Message.objects.create(user=user, chat=chat)
        
        # decode image and save it
        files_list = []
        if files:
            for file, name in files:
                form, imgstr = file.split(';base64,') 
                data = ContentFile(base64.b64decode(imgstr), name=name)
                files_list.append(MessageImages(message=message_obj, file=data))
            MessageImages.objects.bulk_create(files_list)

        if message_obj.chat.__class__ == RoomChat:
            for __user in users:
                r.sadd(f'user:{__user.username}:room_unread', message_obj.id)
        else:
            r.sadd(f'user:{users.username}:chat_unread', message_obj.id)

    @database_sync_to_async
    def clear_messages(self, url, chat_id):
        if url == 'room':
            obj = RoomChat.objects.get(id=chat_id)
            obj.messages.all().delete()
        else:
            obj = PrivateChat.objects.get(id=chat_id)
            obj.messages.all().delete()

    @database_sync_to_async
    def leave_room(self, room_id, username):
        room = RoomChat.objects.get(id=room_id)
        room.users.remove(User.objects.get(username=username))
        if room.users.count() < 2:
            room.delete()

    @database_sync_to_async
    def remove_chat(self, room_id):
        room = PrivateChat.objects.get(id=room_id)
        room.delete()


class ChatAPIConsumer(ObserverModelInstanceMixin, GenericAsyncAPIConsumer):
    lookup_field = 'pk'

    def get_queryset(self, **kwargs):
        view = self.scope['path']
        if 'room' in view:
            return RoomChat.objects.all()
        return PrivateChat.objects.all()

    def get_serializer_class(self, **kwargs) -> type[Serializer]:
        view = self.scope['path']
        if 'room' in view:
            return RoomChatSerializer
        return PrivateChatSerializer
        
    def get_serializer_context(self, **kwargs):
        context = super().get_serializer_context(**kwargs)
        context['user_id'] = self.scope['user'].id
        return context

    @action()
    async def leave_room(self, pk, **kwargs):
        await self.remove_user_from_room(pk)

    @action()
    async def create_message(self, url, message, pk, **kwargs):
        if url == 'room':
            room = await self.get_room(pk=pk)
        else:
            room = await self.get_chat(pk=pk)
        await database_sync_to_async(Message.objects.create)(
            chat=room,
            user=self.scope['user'],
            content=message
        )

    @action()
    async def clear_messages(self, url, pk, **kwargs):
        if url == 'chat':
            chat = await self.get_chat(pk=pk)
        else:
            chat = await self.get_room(pk=pk)
        res = chat.messages.all()
        await database_sync_to_async(res.delete)()

    @action()
    async def remove_user(self, pk, user_id=None, **kwargs):
        await self.remove_user_from_room(pk, user_id)

    @action()
    async def add_user(self, pk, user_id, **kwargs):
        await self.add_user_to_room(pk, user_id)

    @action()
    async def subscribe_to_messages_in_room(self, pk, request_id, **kwargs):
        await self.message_activity.subscribe(room=pk, request_id=request_id)

    @model_observer(Message)
    async def message_activity(
        self,
        message,
        observer=None,
        subscribing_request_ids = [],
        **kwargs
    ):
        for request_id in subscribing_request_ids:
            message_body = dict(request_id=request_id)
            message_body.update(message)
            await self.send_json(message_body)

    @message_activity.groups_for_signal
    def message_activity(self, instance: Message, **kwargs):
        yield f'obj__{instance.object_id}'
        yield f'id__{instance.pk}'

    @message_activity.groups_for_consumer
    def message_activity(self, obj=None, **kwargs):
        if obj is not None:
            yield f'obj__{obj}'

    @message_activity.serializer
    def message_activity(self, instance: Message, action, **kwargs):
        return dict(data=MessageSerializer(instance).data, action=action.value, pk=instance.pk)

    @database_sync_to_async
    def get_room(self, pk):
        return RoomChat.objects.get(pk=pk)

    @database_sync_to_async
    def get_chat(self, pk):
        return PrivateChat.objects.get(pk=pk)

    @database_sync_to_async
    def add_user_to_room(self, pk, user_id):
        room = RoomChat.objects.get(pk=pk)
        room.users.add(User.objects.get(id=user_id))

    @database_sync_to_async
    def remove_user_from_room(self, room_id, user_id=None):
        room = RoomChat.objects.get(id=room_id)
        if user_id:
            room.users.remove(User.objects.get(id=user_id))
        else:
            room.users.remove(User.objects.get(id=self.scope['user'].id))
        if room.users.count() < 2:
            room.delete()
