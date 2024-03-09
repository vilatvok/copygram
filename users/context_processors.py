import redis

from users.models import Action

from django.db.models import Q


r = redis.Redis(host='redis', port=6379, db=0)


def unread_actions(request):
    if request.user.is_authenticated:
        actions = Action.objects.filter(
            Q(post__owner=request.user) |
            Q(user=request.user),
            unread=True
        ).select_related('owner', 'content_type').count()
    else:
        actions = 0
    return {'unread_actions': actions}


def unread_room_messages(request):
    user = request.user
    if user.is_authenticated:
        messages = r.scard(f'user:{user.username}:room_unread')
    else:
        messages = 0
    return {'unread_room_messages': messages}


def unread_chat_messages(request):
    user = request.user
    if user.is_authenticated:
        messages = r.scard(f'user:{user.username}:chat_unread')
    else:
        messages = 0
    return {'unread_chat_messages': messages}