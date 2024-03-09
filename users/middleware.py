from django.shortcuts import redirect
from django.urls import reverse
from django.conf import settings


allowed = [
    reverse(settings.LOGIN_URL), 
    reverse('users:register'), 
    reverse('mainsite:posts'),
]

class LoginRequiredMiddleware:
    """Require login from all templates views."""

    def __init__(self, get_response):
        self.get_response = get_response
        
    def __call__(self, request):
        allowed_domen = (
            any([
                request.path.startswith('/api'), 
                request.path.startswith('/social'), 
                request.path.startswith(settings.MEDIA_URL)
            ])
        )
        if (not request.user.is_authenticated
            and request.path not in allowed
            and not allowed_domen):
            return redirect(settings.LOGIN_URL)
        return self.get_response(request)