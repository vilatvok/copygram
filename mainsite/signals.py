from django.db.models.signals import m2m_changed, post_delete, post_save
from django.dispatch import receiver
from django.core.cache import cache
from django.conf import settings

from .models import Post

@receiver(m2m_changed, sender=Post.is_like.through)
def like_changed(instance, *args, **kwargs):
    instance.total_likes = instance.is_like.count()
    instance.save()
    
@receiver(post_save, sender=Post)
def post_save_cache(*args, **kwargs):
    cache.delete(settings.TOTAL)

@receiver(post_delete, sender=Post)
def post_delete_cache(*args, **kwargs):
    cache.delete(settings.TOTAL)