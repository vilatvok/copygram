from django.db.models.signals import post_delete
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings

from blogs.models import Post


@receiver(post_delete, sender=Post)
def post_delete_cache(*args, **kwargs):
    cache.delete(settings.TOTAL)
