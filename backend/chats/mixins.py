from django.views.generic.detail import DetailView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common import redis_client
from chats.api.serializers import MessageSerializer


class ChatMixin(DetailView):
    template_name = 'chats/chat.html'
    url_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url'] = self.url_name
        context['messages'] = (
            self.object.messages.
            order_by('created_at').
            select_related('user', 'content_type').
            prefetch_related('files')
        )
        values = [message.id for message in context['messages']]
        username = self.request.user.username
        if self.url_name == 'private_chat':
            key = f'user:{username}:private_unread'
        else:
            key = f'user:{username}:group_unread'
        if len(values):
            redis_client.srem(key, *values)
        return context


class ChatAPIMixin:
    permission_classes = [IsAuthenticated]

    def get_serializer_context(self):
        context = super().get_serializer_context()
        context['user_id'] = self.request.user.id
        return context

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, exclude=['id'])
        messages = (
            instance.messages.
            select_related('user', 'content_type').
            prefetch_related('files')
        )
        message_serializer = MessageSerializer(messages, many=True)
        result = {**serializer.data, 'messages': message_serializer.data}
        return Response(result)
