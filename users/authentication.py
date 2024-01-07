from django.contrib.auth.backends import BaseBackend
from django.contrib.auth import get_user_model

# from django.contrib.auth.base_user import AbstractBaseUser


class EmailBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_model()
        try:
            user = user.objects.get(email=username)
            if user.check_password(password):
                return user
        except (user.DoesNotExist, user.MultipleObjectsReturned):
            return

    def get_user(self, user_id):
        try:
            return get_user_model().objects.get(pk=user_id)
        except:
            return


class PhoneBackend(BaseBackend):
    def authenticate(self, request, username=None, password=None, **kwargs):
        user = get_user_model()
        try:
            user = user.objects.get(phone=username)
            if user.check_password(password):
                return user
        except (user.DoesNotExist, user.MultipleObjectsReturned):
            return

    def get_user(self, user_id):
        try:
            return get_user_model().objects.get(pk=user_id)
        except:
            return
