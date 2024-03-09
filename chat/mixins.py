import redis

from django.views.generic.detail import DetailView


r = redis.Redis(host='redis', port=6379, db=0)


class BaseChatMixin(DetailView):
    template_name = 'chat/chat.html'
    pk_url_kwarg = 'chat_id'
    url_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url'] = self.url_name
        context['messages'] = (
            self.object.messages.all().order_by('timestamp').
            select_related('user', 'content_type').prefetch_related('files')
        )
        r.srem(
            f'user:{self.request.user.username}:room_unread', 
            *[message.id for message in context['messages']]
        )
        return context