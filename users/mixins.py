from django.views.generic.list import ListView

from common.utils import redis_client, get_blocked_users

from users.models import User


class FollowersMixin(ListView):
    template_name = 'users/followers.html'
    context_object_name = 'users'
    slug_url_kwarg = 'user_slug'

    def get_queryset(self):
        request = self.request
        blocked_users = get_blocked_users(request.user)
        queryset = (
            User.objects.annotated(current_user=request.user).
            exclude(id__in=blocked_users)
        )
        return queryset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        user_slug = self.kwargs['user_slug']
        context['current_user'] = User.objects.get(slug=user_slug)
        authenticated_user = self.request.user
        requests = []
        for user in context['users']:
            key = f'user:{user.id}:requests'
            user_requests = redis_client.smembers(key)
            if str(authenticated_user.id) in user_requests:
                requests.append(user.id)

        context['user_requests'] = requests
        return context
