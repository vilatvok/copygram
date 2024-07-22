from django.db import transaction
from django.db.models import Case, When, Value, BooleanField
from django.core.cache import cache

from common.utils import create_action, get_blocked_users, redis_client
from blogs.models import Post, Story
from users.models import Archive


def like_post(user, post):
    if post.likes.filter(id=user.id).exists():
        post.likes.remove(user)
        status = 'Unliked'
    # if post has been already liked, then unlike post.
    else:
        with transaction.atomic():
            post.likes.add(user)
            if user != post.owner:
                create_action(user, 'liked post', post, post.file)
        status = 'Liked'
    post.save()
    return status


def save_post(user, post):
    if post.saved.filter(id=user.id).exists():
        post.saved.remove(user)
        status = 'Removed'
    else:
        post.saved.add(user)
        status = 'Saved'
    post.save()
    return status


def get_posts(user=None):
    vip_users = redis_client.smembers('active_vip_users')

    posts = (
        Post.objects.annotated().
        annotate(
            is_vip=Case(
                When(owner_id__in=vip_users, then=Value(True)),
                default=Value(False),
                output_field=BooleanField()
            )
        ).
        exclude(archived=True).
        select_related('owner').
        prefetch_related('tags').
        order_by('-is_vip', '?')
    )

    if user:
        blocked_users = get_blocked_users(user)
        posts = posts.exclude(owner__in=blocked_users)

    return posts


def get_archived_posts(user):
    key = 'archived_posts'
    posts = cache.get(key)
    if posts is None:
        archive = Archive.objects.filter(
            post__owner=user,
            post__archived=True,
        )
        posts_ids = archive.values_list('object_id', flat=True)
        posts = Post.objects.annotated().filter(id__in=posts_ids)
        cache.set(key, posts, 60 * 60)
    return posts


def get_archived_stories(user):
    key = 'archived_stories'
    stories = cache.get(key)
    if stories is None:
        archive = Archive.objects.filter(
            story__owner=user,
            story__archived=True,
        )
        stories_ids = archive.values_list('object_id', flat=True)
        stories = Story.objects.filter(id__in=stories_ids)
        cache.set(key, stories, 60 * 60)
    return stories
