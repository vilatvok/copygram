from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.db.models.signals import post_save
from django.dispatch import receiver

from users.models import User, UserPrivacy


@receiver(user_logged_in, sender=User)
def set_online(user, **kwargs):
    user.is_online = True
    user.save()


@receiver(user_logged_out, sender=User)
def set_offline(user, **kwargs):
    user.is_online = False
    user.save()


@receiver(post_save, sender=User)
def create_user_privacy(instance, created, **kwargs):
    if created:
        UserPrivacy.objects.create(user_id=instance.id)
