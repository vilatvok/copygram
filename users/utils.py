import redis

from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.utils.encoding import force_bytes
from django.core.mail import send_mail

from users.models import Follower


User = get_user_model()
r = redis.Redis(host='redis', port=6379, db=0)


def set_blocked(user, request):
    block_from = user.block_from.all().values_list('block_to', flat=True)
    block_to = user.block_to.all().values_list('block_from', flat=True)
    request.session['blocked'] = list(block_from) + list(block_to)


def send_token_email(user, token):
    uid = urlsafe_base64_encode(force_bytes(user))
    send_mail(
        'Password reset',
        'Click here to reset your password:' +
        f'http://127.0.0.1:8000/api/password-reset-confirm/{uid}/{token}/',
        'kvydyk@gmail.com',
        [user.email]    
    )
    

class Recommender:
    """
    Recommendations for user.
    Base on user's followers. 
    """

    def get_key(self, user):
        return f'user:{user.id}:recommend'
    
    def add_suggestions(self, user, others):
        result = []
        for other in others:
            if not Follower.objects.filter(user_from=user, user_to=other).exists():
                result.append(other.id)
        if len(result):
            r.sadd(self.get_key(user), *result)

    def remove_suggestions(self, user, others):
        if len(others):
            users = [other.id for other in others]
            r.srem(self.get_key(user), *users)
    
    def suggests_for_user(self, user):
        suggestions = r.smembers(self.get_key(user))
        suggestions_users_ids = [int(s) for s in suggestions]
        suggestions_users = User.objects.filter(id__in=suggestions_users_ids)
        return suggestions_users
