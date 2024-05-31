from django.db import models
from django.contrib.auth.models import UserManager


class CustomUserManager(UserManager):
    def blocked(self, user):
        return self.get_queryset().filter(blocked_by__block_from=user)

    def annotated(self, current_user):
        from users.models import Follower
        is_followed = Follower.objects.filter(
            from_user=current_user,
            to_user=models.OuterRef('pk'),
        ).select_related('from_user', 'to_user')
        users = self.annotate(
            followers_count=models.Count('followers', distinct=True),
            following_count=models.Count('following', distinct=True),
            is_followed=models.Exists(is_followed),
        )
        return users
