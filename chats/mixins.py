from django.views.generic.detail import DetailView

from common.utils import redis_client


class BaseChatMixin(DetailView):
    template_name = 'chats/chat.html'
    pk_url_kwarg = 'chat_id'
    url_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url'] = self.url_name
        context['messages'] = (
            self.object.messages.all().order_by('timestamp').
            select_related('user', 'content_type').prefetch_related('files')
        )
        values = [message.id for message in context['messages']]
        user_id = self.request.user.id
        if self.url_name == 'chat':
            key = f'user:{user_id}:chat_unread'
        else:
            key = f'user:{user_id}:room_unread'
        if len(values):
            redis_client.srem(key, *values)
        return context
