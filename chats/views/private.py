from django.db.models import Q
from django.shortcuts import redirect
from django.core.exceptions import PermissionDenied
from django.views import View
from django.views.generic.list import ListView

from chats.mixins import ChatMixin
from chats.models import PrivateChat

from users.models import User


class PrivateChatsView(ListView):
    template_name = 'chats/chats.html'
    context_object_name = 'chats'

    def get_queryset(self):
        user = self.request.user        
        qs = PrivateChat.objects.annotated().filter(
            Q(first_user=user) |
            Q(second_user=user),
        ).select_related('first_user', 'second_user')
        return qs


class PrivateChatView(ChatMixin):
    queryset = PrivateChat.objects.select_related('first_user', 'second_user')
    url_name = 'chat'
    context_object_name = 'chat'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        user = request.user
        if user not in [self.object.first_user, self.object.second_user]:
            raise PermissionDenied("You can't enter this chat")
        return response


class CreatePrivateChatView(View):
    def post(self, request, user_slug):
        user = User.objects.get(slug=user_slug)
        obj = PrivateChat.objects.create(
            first_user=request.user,
            second_user=user,
        )
        return redirect('chats:private_chat', obj.id)
