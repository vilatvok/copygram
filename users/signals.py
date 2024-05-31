from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.cache import cache
from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver

from users.models import Block, User, UserPrivacy


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


@receiver([post_save, post_delete], sender=Block)
def cache_blocked(*args, **kwargs):
    cache.delete_many(['blocked_from', 'blocked_by'])
