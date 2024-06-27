from django.db import transaction
from django.http import JsonResponse
from django.shortcuts import redirect
from django.views import View

from common.utils import redis_client

from users.models import User
from users.mixins import FollowersMixin
from users.models import Action, Follower
from users.utils import follow_to_user


class FollowersView(FollowersMixin):
    extra_context = {'title': 'followers'}

    def get_queryset(self):
        qs = super().get_queryset()
        user_slug = self.kwargs['user_slug']
        queryset = qs.filter(following__to_user__slug=user_slug)
        return queryset


class FollowingView(FollowersMixin):
    extra_context = {'title': 'following'}

    def get_queryset(self):
        qs = super().get_queryset()
        user_slug = self.kwargs['user_slug']
        queryset = qs.filter(followers__from_user__slug=user_slug)
        return queryset


class FollowToUserView(View):
    """
    Is used for following another user.
    Creates recommendations, base on user's followers.
    If the user has been already followed to another user then
    cancel this following and delete user's followers from recommendations.
    """

    def post(self, request, user_slug):
        from_user = request.user
        to_user = User.objects.get(slug=user_slug)
        response = follow_to_user(from_user, to_user)
        return JsonResponse({'status': response})


class AcceptFollowerView(View):
    def post(self, request, user_slug):
        from_user = User.objects.get(slug=user_slug)
        to_user = request.user
        with transaction.atomic():
            Follower.objects.create(from_user=from_user, to_user=to_user)
            Action.objects.filter(
                owner=from_user,
                user=to_user,
                act='wants to follow to you',
            ).delete()
        redis_client.srem(f'user:{to_user.id}:requests', from_user.id)
        return redirect('users:actions')
    

class RejectFollowerView(View):
    def post(self, request, user_slug):
        from_user = User.objects.get(slug=user_slug)
        to_user = request.user
        Action.objects.filter(
            owner=from_user,
            user=to_user,
            act='wants to follow to you',
        ).delete()
        redis_client.srem(f'user:{to_user.id}:requests', from_user.id)
        return redirect('users:actions')
