from django.db import models
from django.views.generic.list import ListView

from common.utils import redis_client

from users.models import Follower, User


class FollowersMixin(ListView):
    context_object_name = 'users'
    slug_url_kwarg = 'user_slug'

    def get_queryset(self):
        is_followed = Follower.objects.filter(
            from_user=self.request.user,
            to_user=models.OuterRef('pk'),
        )
        queryset = (
            User.objects.exclude(id__in=self.request.session['blocked']).
            annotate(
                followers_count=models.Count('followers', distinct=True),
                is_followed=models.Exists(is_followed),
            )
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['current_user'] = User.objects.get(
            slug=self.kwargs['user_slug'],
        )

        authenticated_user = self.request.user
        requests = []
        for user in self.get_queryset():
            key = f'user:{user.id}:requests'
            user_requests = redis_client.smembers(key)
            if str(authenticated_user.id) in user_requests:
                requests.append(user.id)

        context['user_requests'] = requests
        return context
