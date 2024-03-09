from django.utils import timezone
from django.contrib.contenttypes.models import ContentType
from django.db.models import Value, Subquery, CharField, OuterRef
from django.db.models.functions import Concat
from django.conf import settings 

from datetime import timedelta

from mainsite.models import PostMedia, Post
from users.models import Action


def create_action(owner, act, file=None, target=None):
    """Create action if there is no similar actions (5 minutes)."""
    inter = timezone.now() - timedelta(minutes=5)
    similar = Action.objects.filter(owner=owner, act=act, file=file, date__gte=inter)

    similar_actions = None
    if target:
        target_ct = ContentType.objects.get_for_model(target)
        similar_actions = similar.filter(content_type=target_ct, object_id=target.id)

    if not similar_actions:
        action = Action.objects.create(owner=owner, act=act, file=file, target=target)
        action.save()


def get_posts(user=None, blocked=None):
    subquery = PostMedia.objects.filter(post=OuterRef('pk')).values('file')[:1]
    if blocked is not None:
        queryset = (
            Post.objects.select_related('owner').prefetch_related('tags').
            exclude(owner__in=blocked).
            annotate(file=Concat(
                Value(settings.MEDIA_URL), 
                Subquery(subquery, output_field=CharField())
            ))
        )
    else:
        queryset = (
            Post.objects.select_related('owner').prefetch_related('tags').
            filter(owner=user).
            annotate(file=Concat(
                Value(settings.MEDIA_URL), 
                Subquery(subquery, output_field=CharField())
            ))
        )
    return queryset


def set_serializer_fields(fields, old_fields):
    allowed = set(fields)
    old = set(old_fields)
    for field in old.intersection(allowed):
        old_fields.pop(field)
