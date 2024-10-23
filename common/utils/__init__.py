from redis import Redis

from datetime import timedelta

from django.utils import timezone
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType

from rest_framework import mixins
from rest_framework.viewsets import GenericViewSet
from rest_framework.fields import empty
from rest_framework.serializers import BaseSerializer

from users.models import Action


redis_client = Redis(
    host='redis',
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


def get_blocked_users(user):
    key1 = 'blocked_from'
    key2 = 'blocked_by'
    blocked = cache.get(key1)
    blocked_by = cache.get(key2)
    if blocked is None:
        blocked = user.blocked.values_list('block_to', flat=True)
        cache.set(key1, blocked, 60 * 60)
    if blocked_by is None:
        blocked_by = user.blocked_by.values_list('block_from', flat=True)
        cache.set(key2, blocked_by, 60 * 60)
    return list(blocked) + list(blocked_by)


def set_serializer_fields(fields, old_fields):
    allowed = set(fields)
    old = set(old_fields)
    for field in old.intersection(allowed):
        old_fields.pop(field)


def cache_queryset(name, timeout=5):
    def decorator(func):
        def wrapper(*args, **kwargs):
            objs = cache.get(name)
            if objs is None:
                objs = func(*args, **kwargs)
                cache.set(name, objs, timeout)
            return objs
        return wrapper
    return decorator


def get_user_ip(request):
    req_headers = request.META
    x_forwarded_for = req_headers.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        ip_addr = x_forwarded_for.split(',')[-1].strip()
    else:
        ip_addr = req_headers.get('REMOTE_ADDR')
    return ip_addr


class CustomSerializer(BaseSerializer):
    def __init__(self, instance=None, data=empty, **kwargs):
        fields = kwargs.pop('exclude', None)
        super().__init__(instance, data, **kwargs)
        if fields:
            set_serializer_fields(fields, self.fields)


class NonUpdateViewSet(mixins.ListModelMixin,
                        mixins.RetrieveModelMixin,
                        mixins.CreateModelMixin,
                        mixins.DestroyModelMixin,
                        GenericViewSet):
    pass
