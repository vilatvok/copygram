from django.db import transaction
from django.db.models import Q, Count, Subquery, OuterRef
from django.http import Http404
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.contrib.auth import get_user_model
from django.core.exceptions import PermissionDenied
from django.views import View
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from chats.mixins import BaseChatMixin
from chats.models import Message, RoomChat, PrivateChat
from chats.forms import RoomForm, EditRoomForm


User = get_user_model()


class PrivateChatsView(ListView):
    template_name = 'chats/chats.html'
    context_object_name = 'chats'

    def get_queryset(self):
        # Retrieve information about the last message to show it in template
        last_message_user = (
            Message.objects.filter(object_id=OuterRef('pk')).
            order_by('-timestamp').values('user__username')[:1]
        )
        last_message = (
            Message.objects.filter(object_id=OuterRef('pk')).
            order_by('-timestamp').values('content')[:1]
        )

        # Annotate objects with last message
        return PrivateChat.objects.filter(
            Q(first_user=self.request.user) | Q(second_user=self.request.user)
        ).annotate(
            last_message_user=Subquery(last_message_user),
            last_message=Subquery(last_message),
        ).select_related('first_user', 'second_user')


class RoomChatsView(ListView):
    template_name = 'chats/rooms.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        return RoomChat.objects.only('id', 'name', 'messages').filter(
            users__in=[self.request.user],
        )


class PrivateChatView(BaseChatMixin):
    model = PrivateChat
    url_name = 'chat'
    context_object_name = 'chat'

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        try:
            chat = self.get_object()
        except PrivateChat.DoesNotExist:
            raise Http404('Not found or this chat was deleted')
        if user not in [chat.first_user, chat.second_user]:
            raise PermissionDenied("You can't see this chat")
        return super().dispatch(request, *args, **kwargs)


class RoomChatView(BaseChatMixin):
    model = RoomChat
    url_name = 'room'
    context_object_name = 'chat'

    def dispatch(self, request, *args, **kwargs):
        user = request.user
        room = self.get_object()
        if user not in room.users.all():
            raise PermissionDenied("You can't see this room")
        return super().dispatch(request, *args, **kwargs)


class CreateRoomView(CreateView):
    model = RoomChat
    form_class = RoomForm
    template_name = 'chats/create_room.html'

    def get_success_url(self):
        return reverse_lazy('chats:room_chat', args=[self.object.id])

    @transaction.atomic
    def form_valid(self, form):
        f = form.save(commit=False)
        f.owner = self.request.user
        response = super().form_valid(form)
        self.object.users.add(self.request.user)
        return response

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        users = User.objects.exclude(id=self.request.user.id)
        kwargs['queryset'] = users
        return kwargs


class RoomUsersView(ListView):
    template_name = 'users/followers.html'
    context_object_name = 'users'
    pk_url_kwarg = 'room_id'

    def get_queryset(self):
        room = RoomChat.objects.only('users').get(id=self.kwargs['room_id'])
        query = room.users.all()
        return query.annotate(follower_count=Count('followers'))


class EditRoomView(UpdateView):
    model = RoomChat
    form_class = EditRoomForm
    template_name = 'chats/edit_room.html'
    pk_url_kwarg = 'room_id'

    def dispatch(self, request, *args, **kwargs):
        room = self.get_object()
        if room.owner != request.user:
            raise PermissionDenied('You dont have permission')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        return reverse_lazy('chats:room_chat', args=[self.object.id])

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        users = self.object.users.all()
        add_users = User.objects.exclude(id__in=users)
        kwargs['queryset'] = users
        kwargs['queryset2'] = add_users
        return kwargs

    def form_valid(self, form):
        users = form.cleaned_data['add_users']
        form_instance = form.save(commit=False)
        form_instance.users.add(*users)
        return super().form_valid(form)


class DeleteRoomView(DeleteView):
    model = RoomChat
    template_name = 'chats/rooms.html'
    success_url = reverse_lazy('chats:rooms')
    pk_url_kwarg = 'room_id'


class CreatePrivateChatView(View):
    def post(self, request, user_slug):
        user = User.objects.get(slug=user_slug)
        obj = PrivateChat.objects.create(
            first_user=request.user,
            second_user=user,
        )
        return redirect('chats:private_chat', obj.id)
