from django.views.generic.detail import DetailView


class BaseChatMixin(DetailView):
    template_name = 'chat/chat.html'
    pk_url_kwarg = 'chat_id'
    url_name = None

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['url'] = self.url_name
        context['messages'] = self.object.messages.all()
        return context