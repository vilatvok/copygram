from users.models import Action

from django.db.models import Q


def unread_messages(request):
    if request.user.is_authenticated:
        actions = Action.objects.filter(
            Q(post__owner=request.user) |
            Q(user=request.user),
            unread=True
        ).select_related('owner', 'content_type').count()
    else:
        actions = 0
    return {'unread_messages': actions}