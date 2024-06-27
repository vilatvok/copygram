from django.db import models
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.views import View
from django.views.generic.detail import DetailView
from django.views.generic.edit import UpdateView, DeleteView
from django.views.generic.list import ListView

from two_factor.utils import default_device

from common.utils import redis_client, get_blocked_users

from users.forms import UserEditForm, UserPrivacyForm
from users.models import User, Block, Follower, UserPrivacy
from users.utils import Recommender, block_user, get_user_posts

from blogs.models import Story

from chats.models import PrivateChat


class ProfileView(DetailView):
    """Show user profile."""

    model = User
    template_name = 'users/profile.html'
    context_object_name = 'user'
    slug_url_kwarg = 'user_slug'

    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        user = self.object
        current_user = request.user
        if user != current_user:
            is_blocked = Block.objects.filter(
                models.Q(block_from=current_user, block_to=user) |
                models.Q(block_from=user, block_to=current_user),
            ).exists()
            if is_blocked:
                return redirect('users:profile', current_user.slug)
        return response

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user = self.object
        current_user = self.request.user

        context['posts'] = get_user_posts(user=user)
        context['followers'] = user.followers.count()
        context['following'] = user.following.count()

        key = f'user:{user.id}:requests'
        user_requests = redis_client.smembers(key)
        if str(current_user.id) in user_requests:
            context['request_to_follow'] = True
        else:
            context['request_to_follow'] = False

        context['is_followed'] = Follower.objects.filter(
            from_user=current_user,
            to_user=user,
        ).exists()

        # check if chat has been alredy created
        # if not, then call (create_chat) in chat app
        chat = PrivateChat.objects.filter(
            models.Q(first_user=user, second_user=current_user) |
            models.Q(first_user=current_user, second_user=user),
        ).select_related('first_user', 'second_user')

        context['is_chat'] = False
        if chat.exists():
            context['is_chat'] = chat[0]

        blocked_users = get_blocked_users(current_user)
        context['stories'] = (
            Story.objects.filter(owner=user).
            exclude(owner__in=blocked_users, archived=True).
            select_related('owner')
        )

        # recommendations for user
        recommender = Recommender()
        context['suggestions'] = recommender.suggests_for_user(user)
        return context


class EditProfileView(UpdateView):
    model = User
    form_class = UserEditForm
    template_name = 'users/edit_profile.html'

    def get_object(self, queryset=None):
        return self.request.user

    def get_success_url(self):
        return self.object.get_absolute_url()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['is_enable'] = True if default_device(self.object) else False
        return context


class DeleteProfileView(DeleteView):
    model = User
    success_url = reverse_lazy('users:login')

    def get_object(self, queryset=None):
        return self.request.user


class SettingsView(UpdateView):
    model = UserPrivacy
    form_class = UserPrivacyForm
    template_name = 'users/settings.html'

    def get_object(self, queryset=None):
        return UserPrivacy.objects.get(user_id=self.request.user.id)

    def get_success_url(self):
        user = self.request.user
        return user.get_absolute_url()


class BlockedView(ListView):
    """Blocked users."""

    template_name = 'users/blocked.html'
    context_object_name = 'users'

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.blocked(user=user)
        return queryset


class BlockUserView(View):
    """
    Block the user and delete all connections between users.
    Otherwise, unblock the user.
    """

    def post(self, request, user_slug):
        user = request.user
        to_user = User.objects.get(slug=user_slug)
        block_user(user, to_user)
        return redirect('users:profile', user_slug)
