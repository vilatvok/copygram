import json

from channels.generic.websocket import AsyncWebsocketConsumer


class UserStatusConsumer(AsyncWebsocketConsumer):
    connected_users = []

    async def connect(self):
        self.user = self.scope['user']
        self.connected_users.append(self.user.username)
        await self.channel_layer.group_add('users', self.channel_name)
        await self.accept()

    async def disconnect(self, code):
        self.connected_users.remove(self.user.username)
        await self.channel_layer.group_discard('users', self.channel_name)

    async def receive(self, text_data):
        data = json.loads(text_data)
        user = data['user']
        status = data['status']
        await self.channel_layer.group_send(
            'users',
            {
                'type': 'set_status',
                'user': user,
                'status': status,
                'users': self.connected_users
            }
        )
    
    async def set_status(self, event):
        await self.send(text_data=json.dumps(event))
