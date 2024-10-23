from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.contrib.auth.signals import user_logged_in, user_logged_out
from django.core.cache import cache
from django.db.models import Count, Q

from common.utils import redis_client

from users.models import Archive, Block, User, UserPrivacy
from users.tasks import delete_account_scheduler


@receiver(user_logged_in, sender=User)
def set_online_status(user, **kwargs):
    user.is_online = True
    user.save()
    # Update user recommendations after login.
    redis_key = f'user:{user.id}:recommendations'
    users = redis_client.scard(redis_key)
    if users < 30:
        count = 30 - users
        recommended_users = redis_client.smembers(redis_key)
        recommended_users.add(user.id)
        users = (
            User.objects.
            exclude(Q(id__in=recommended_users) | Q(followers__from_user=user)).
            annotate(followers_count=Count('followers')).
            order_by('-followers_count', '?').
            values_list('id', flat=True)
        )[:count]
        if len(users):
            redis_client.sadd(redis_key, *users)


@receiver(user_logged_out, sender=User)
def set_offline_status(user, **kwargs):
    user.is_online = False
    user.save()


@receiver(post_save, sender=User)
def create_user_privacy(instance, created, **kwargs):
    if created:
        UserPrivacy.objects.create(user_id=instance.id)
        delete_account_scheduler(instance.id)


@receiver([post_save, post_delete], sender=Archive)
def cache_archived(*args, **kwargs):
    cache.delete_many(['archived_posts', 'archived_stories'])


@receiver([post_save, post_delete], sender=Block)
def cache_blocked(*args, **kwargs):
    cache.delete_many(['blocked', 'blocked_by', 'blocked_from'])
