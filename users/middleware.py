from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


class LoginRequiredMiddleware:
    def __init__(self, get_response):
        self.get_response = get_response
        self.allowed = [settings.LOGIN_URL, "users:register"]

    def __call__(self, request):
        if (
            not request.user.is_authenticated
            and request.path not in map(lambda x: reverse(x), self.allowed)
            and not request.path.startswith("/api/")
        ):
            return redirect(settings.LOGIN_URL)
        return self.get_response(request)
