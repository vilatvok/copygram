import pandas as pd

from django.db import transaction, connection
from django.db.models import Q
from django.core.mail import send_mail
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.contrib.auth.tokens import default_token_generator

from common.utils import create_action, redis_client
from users.models import User, Action, Follower, Block
from blogs.models import Comment, Post


class Recommender:
    """
    Recommendations for user.
    Based on user's followers.
    Needs improvement.
    """
    @staticmethod
    def get_key(user):
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
        suggestions_users = (
            User.objects.filter(id__in=suggestions).
            select_related('privacy')
        )
        return suggestions_users


# def sql_to_pandas():
#     with connection.cursor() as cursor:
#         cursor.execute('SELECT * FROM users_user')
#         columns = [col[0] for col in cursor.description]
#         data = cursor.fetchall()
#     return pd.DataFrame(data, columns=columns)


def get_user_posts(user):
    posts = (
        Post.objects.annotated().
        exclude(archived=True).filter(owner=user)
    )
    return posts


def send_reset_email(user, link, ref=None):
    uidb64 = urlsafe_base64_encode(force_bytes(user.pk))
    token = default_token_generator.make_token(user)
    if 'register' in link:
        subject = 'Confirm registration'
        if ref:
            message = (
                'Click here to confirm registration:\n'
                f'{link}/{uidb64}/{token}/?ref={ref}'
            )
        else:
            message = (
                'Click here to confirm registration:\n'
                f'{link}/{uidb64}/{token}/'
            )  
    else:
        subject = 'Reset password'
        message = (
            'Click here to reset password:\n'
            f'{link}/{uidb64}/{token}/'
        )

    send_mail(
        subject=subject,
        message=message,
        from_email='kvydyk@gmail.com',
        recipient_list=[user.email],
    )


def check_token(uidb64, token):
    uid = force_str(urlsafe_base64_decode(uidb64))
    user = User.objects.get(pk=uid)
    is_valid = default_token_generator.check_token(user, token)
    return (user, is_valid)


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
                create_action(from_user, f'followed to you', to_user)
            recommender.add_suggestions(from_user, others)
            recommender.remove_suggestions(from_user, [to_user])
            user_following = User.objects.filter(followers__from_user=from_user)
            user_followers = User.objects.filter(following__to_user=from_user)
            for user in user_followers:
                recommender.add_suggestions(user, user_following)
            return 'Followed'


def block_user(from_user, to_user):
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
