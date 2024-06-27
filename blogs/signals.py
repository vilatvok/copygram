from django.dispatch import receiver
from django.db.models.signals import post_save, post_delete
from django.core.cache import cache

from blogs.models import Post, Story
from blogs.tasks import archive_story_scheduler


@receiver([post_save, post_delete], sender=Post)
def cache_post(*args, **kwargs):
    cache.delete('saved_posts')


@receiver(post_save, sender=Story)
def archive_story(instance, created, *args, **kwargs):
    if created:
        archive_story_scheduler(
            story_id=instance.id,
            story_date=instance.date,
        )
    cache.delete('stories')


@receiver(post_delete, sender=Story)
def archive_story_on_delete(*args, **kwargs):
    cache.delete('stories')
