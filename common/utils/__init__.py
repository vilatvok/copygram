from redis import Redis

from django.conf import settings
from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models.functions import Concat
from django.db.models import Value, Subquery, CharField, OuterRef, Count
from rest_framework.fields import empty

from rest_framework.serializers import BaseSerializer

from datetime import timedelta

from blogs.models import PostMedia, Post
from users.models import Action


redis_client = Redis(
    host='redis',
    port=6379,
    db=0,
    charset='utf-8',
    decode_responses=True,
)


def create_action(owner, act, target, file=None):
    """Create an action if there is no similar actions."""
    
    inter = timezone.now() - timedelta(minutes=5)
    target_ct = ContentType.objects.get_for_model(target)

    similar_actions = Action.objects.filter(
        owner=owner,
        act=act,
        date__gte=inter,
        content_type=target_ct,
        object_id=target.id,
    )

    if not similar_actions:
        action = Action.objects.create(
            owner=owner,
            act=act,
            file=file,
            target=target,
        )
        action.save()

        # add an unread action to redis storage
        try:
            key = f'user:{target.owner.id}:unread_actions'
        except AttributeError:
            key = f'user:{target.id}:unread_actions'
        redis_client.sadd(key, action.id)


def get_posts(user=None, blocked=[]):
    subquery = PostMedia.objects.filter(
        post=OuterRef('pk'),
    ).values('file')[:1]

    if user:
        queryset = (
            Post.objects.filter(owner=user).
            select_related('owner').prefetch_related('tags').
            annotate(
                likes_count=Count('likes'),
                file=Concat(
                    Value(settings.MEDIA_URL),
                    Subquery(subquery, output_field=CharField()),
                ),
            )
        )
    else:
        queryset = (
            Post.objects.exclude(owner__in=blocked).
            select_related('owner').prefetch_related('tags').
            annotate(
                likes_count=Count('likes'),
                file=Concat(
                    Value(settings.MEDIA_URL),
                    Subquery(subquery, output_field=CharField()),
                ),
            )
        )
    return queryset


def set_serializer_fields(fields, old_fields):
    allowed = set(fields)
    old = set(old_fields)
    for field in old.intersection(allowed):
        old_fields.pop(field)


class CustomSerializer(BaseSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(instance, data, **kwargs)
        if fields:
            set_serializer_fields(fields, self.fields)
