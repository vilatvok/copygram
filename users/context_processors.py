from common.utils import redis_client


def unread_actions(request):
    user = request.user
    if user.is_authenticated:
        actions = redis_client.scard(f'user:{user.id}:unread_actions')
    else:
        actions = 0
    return {'unread_actions': actions}


def unread_room_messages(request):
    user = request.user
    if user.is_authenticated:
        messages = redis_client.scard(f'user:{user.id}:room_unread')
    else:
        messages = 0
    return {'unread_room_messages': messages}


def unread_chat_messages(request):
    user = request.user
    if user.is_authenticated:
        messages = redis_client.scard(f'user:{user.id}:chat_unread')
    else:
        messages = 0
    return {'unread_chat_messages': messages}
