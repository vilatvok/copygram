from django.db import transaction
from django.urls import reverse_lazy
from django.core.exceptions import PermissionDenied
from django.views.generic.list import ListView
from django.views.generic.edit import CreateView, UpdateView, DeleteView

from chats.mixins import ChatMixin
from chats.models import RoomChat
from chats.forms import RoomForm, EditRoomForm

from users.models import User


class RoomChatsView(ListView):
    template_name = 'chats/rooms.html'
    context_object_name = 'rooms'

    def get_queryset(self):
        qs = (
            RoomChat.objects.annotated().
            filter(users__in=[self.request.user]).
            select_related('owner')
        )
        return qs


class RoomChatView(ChatMixin):
    queryset = RoomChat.objects.select_related('owner')
    url_name = 'room'
    context_object_name = 'chat'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if request.user not in self.object.users.all():
            raise PermissionDenied("You can't enter this room")
        return response


class RoomUsersView(ListView):
    template_name = 'users/followers.html'
    context_object_name = 'users'
    pk_url_kwarg = 'room_id'

    def get_queryset(self):
        user = self.request.user
        room = RoomChat.objects.only('users').get(id=self.kwargs['room_id'])
        qs = User.objects.annotated(current_user=user).filter(rooms=room)
        return qs


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


class EditRoomView(UpdateView):
    queryset = RoomChat.objects.select_related('owner').prefetch_related('users')
    form_class = EditRoomForm
    template_name = 'chats/edit_room.html'
    pk_url_kwarg = 'room_id'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if self.object.owner != request.user:
            raise PermissionDenied('You dont have permission')
        return response

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

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        if self.object.owner != request.user:
            raise PermissionDenied('You dont have permission')
        return response
