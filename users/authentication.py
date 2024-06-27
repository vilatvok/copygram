from django.contrib.auth.backends import BaseBackend

from users.models import User


class EmailBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = User
        try:
            user = user.objects.get(email=username)
        except (User.DoesNotExist, User.MultipleObjectsReturned):
            return
        else:
            if user.check_password(password):
                return user

    def get_user(self, user_id):
        try:
            return User.objects.get(pk=user_id)
        except User.DoesNotExist:
            return
