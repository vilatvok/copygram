from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.dispatch import receiver

from users.models import User


@receiver(user_logged_in, sender=User)
def set_online(user, **kwargs):
    user.is_online = True
    user.save()


@receiver(user_logged_out, sender=User)
def set_offline(user, **kwargs):
    user.is_online = False
    user.save()
