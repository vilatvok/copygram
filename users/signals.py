from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver
from django.contrib.auth import get_user_model


@receiver(user_logged_in)
def log_status(sender, request, user, **kwargs):
    user_log = get_user_model().objects.get(id=user.id)
    user_log.online = True
    user_log.save()


@receiver(user_logged_out)
def log_status(sender, request, user, **kwargs):
    user_log = get_user_model().objects.get(id=user.id)
    user_log.online = False
    user_log.save()
