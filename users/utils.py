from django.db import transaction
from django.db.models import Q
from django.core.mail import send_mail
from django.utils.encoding import force_bytes
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_encode
from django.contrib.auth.tokens import default_token_generator

from common.utils import create_action, redis_client

from users.models import Action, Follower, Block

from blogs.models import Comment, Post


User = get_user_model()


class Recommender:
    """
    Recommendations for user.
    Based on user's followers.
    """

    def get_key(self, user):
        return f'user:{user.id}:recommendations'

    def add_suggestions(self, user, others):
        result = []
        for other in others:
            obj = Follower.objects.filter(from_user=other, to_user=user)
            if not obj.exists():
                result.append(other.id)
        if len(result):
            redis_client.sadd(self.get_key(user), *result)

    def remove_suggestions(self, user, others):
        if len(others):
            users = [other.id for other in others]
            redis_client.srem(self.get_key(user), *users)

    def suggests_for_user(self, user):
        users = redis_client.smembers(self.get_key(user))
        suggestions = [int(user_id) for user_id in users]
        suggestions_users = User.objects.filter(id__in=suggestions)
        return suggestions_users


def get_user_posts(user):
    posts = (
        Post.objects.annotated().
        exclude(archived=True).filter(owner=user)
    )
    return posts


def send_reset_email(user, link):
    uid = urlsafe_base64_encode(force_bytes(user))
    token = default_token_generator.make_token(user)
    send_mail(
        subject='Password reset',
        message=(
            'Click here to reset your password:\n'
            f'{link}/{uid}/{token}/'
        ),
        from_email='kvydyk@gmail.com',
        recipient_list=[user.email],
    )


def follow_to_user(from_user, to_user):
    is_followed = Follower.objects.filter(
        from_user=from_user,
        to_user=to_user,
    )
    others = (
        User.objects.filter(followers__from_user=to_user).
        exclude(id=from_user.id)
    )

    recommender = Recommender()

    if is_followed.exists():
        is_followed.delete()
        recommender.add_suggestions(from_user, [to_user])
        recommender.remove_suggestions(from_user, others)
        return 'Unfollowed'
    else:
        if to_user.privacy.private_account:
            key = f'user:{to_user.id}:requests'
            user_requests = redis_client.smembers(key)
            if str(from_user.id) in user_requests:
                redis_client.srem(key, from_user.id)
                return 'Canceled'
            else:
                redis_client.sadd(key, from_user.id)
                create_action(from_user, 'wants to follow to you', to_user)
                return 'Request was sent'
        else:
            with transaction.atomic():
                Follower.objects.create(from_user=from_user, to_user=to_user)
                create_action(from_user, 'followed to you', to_user)
            recommender.add_suggestions(from_user, others)
            recommender.remove_suggestions(from_user, [to_user])
            user_following = User.objects.filter(followers__from_user=from_user)
            user_followers = User.objects.filter(following__to_user=from_user)
            for user in user_followers:
                recommender.add_suggestions(user, user_following)
            return 'Followed'


def block_user(request, from_user, to_user):
    is_blocked = Block.objects.filter(block_from=from_user, block_to=to_user)
    if is_blocked.exists():
        is_blocked.delete()
        return 'Unblocked'
    else:
        with transaction.atomic():
            Block.objects.create(block_from=from_user, block_to=to_user)

            posts = from_user.likes.filter(owner=to_user)
            user_posts = to_user.likes.filter(owner=from_user)

            for post in posts:
                post.likes.remove(from_user)
            for post in user_posts:
                post.likes.remove(to_user)

            Comment.objects.filter(
                Q(owner=to_user, post__owner=from_user) |
                Q(owner=from_user, post__owner=to_user)
            ).delete()

            Follower.objects.filter(
                Q(from_user=to_user, to_user=from_user) |
                Q(from_user=from_user, to_user=to_user)
            ).delete()

            Action.objects.filter(
                Q(owner=to_user, post__owner=from_user) |
                Q(owner=to_user, user=from_user) |
                Q(owner=from_user, post__owner=to_user) |
                Q(owner=from_user, user=to_user)
            ).delete()
            return 'Blocked'
