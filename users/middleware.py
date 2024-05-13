from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class LoginRequiredMiddleware:
    """Require login from all templates views."""

    def __init__(self, get_response):
        self.get_response = get_response    

    def __call__(self, request):
        allowed_paths = [
            reverse(settings.LOGIN_URL),
            reverse('users:register'),
            reverse('blogs:posts'),
        ]

        allowed_domens = [
            request.path.startswith('/api'),
            request.path.startswith('/social'),
            request.path.startswith('/password'),
            request.path.startswith(settings.MEDIA_URL),
        ]

        statement = (
            not request.user.is_authenticated
            and request.path not in allowed_paths
            and not any(allowed_domens)
        )
        if (statement):
            return redirect(settings.LOGIN_URL)
        return self.get_response(request)
