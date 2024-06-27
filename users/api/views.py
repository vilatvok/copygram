import json

from datetime import timedelta, datetime

from django.db import transaction
from django.db.models import Q
from django.conf import settings
from django.core.cache import cache
from django.utils.decorators import method_decorator
from django.core.mail import send_mail

from django_filters.rest_framework import DjangoFilterBackend

from django_celery_beat.models import PeriodicTask, CrontabSchedule

from rest_framework import status, mixins
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet, GenericViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated

from common.utils import cache_queryset, redis_client, get_blocked_users

from users.mixins import ListModelViewSet
from users.api import serializers
from users.permissions import IsOwner
from users.models import User, Action, Follower, Referral
from users.utils import (
    Recommender,
    block_user,
    check_token,
    follow_to_user,
    get_user_posts,
    send_reset_email,
)

from blogs.models import Post, Story
from blogs.api.serializers import (
    PostSerializer,
    StorySerializer,
    CommentSerializer,
)


##############################################
# USER
class UserViewSet(ModelViewSet):
    lookup_field = 'slug'
    permission_classes = [IsOwner]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['username', 'first_name', 'last_name']

    def get_serializer_class(self):
        if self.action in ['create']:
            return serializers.UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return serializers.UserUpdateSerializer
        return serializers.UserSerializer

    def get_queryset(self):
        request = self.request
        blocked_users = get_blocked_users(request.user)
        queryset = (
            User.objects.annotated(current_user=request.user).
            exclude(id__in=blocked_users).
            select_related('privacy')
        )
        return queryset

    def get_followers_view(self, request, view_name):
        user = self.get_object()
        qs = self.get_queryset()
        if view_name == 'followers':
            queryset = qs.filter(following__to_user=user)
        else:
            queryset = qs.filter(followers__from_user=user)

        serializer = serializers.UserSerializer(
            instance=queryset,
            many=True,
            context={'request': request},
            exclude=['phone', 'last_login'],
        )
        return Response(serializer.data)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save()
            return Response({'status': 'Check your email for confirmation'})
        else:
            user = User.objects.filter(email=serializer.data['email'])
            if user.exists():
                return Response(
                    {'status': "You've already filled this form, check email"}
                )
            return Response(serializer.errors)

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        page = self.paginate_queryset(queryset)
        serializer = self.get_serializer(
            instance=page,
            many=True,
            exclude=['gender', 'bio', 'last_login'],
        )
        return self.get_paginated_response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        user = self.get_object()
        serializer = self.get_serializer(user)
        return Response(serializer.data)

    @action(detail=True)
    def posts(self, request, slug=None):
        post = get_user_posts(user=self.get_object())
        serializer = PostSerializer(
            instance=post,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(detail=True)
    def stories(self, request, slug=None):
        story = (
            Story.objects.filter(owner=self.get_object()).
            select_related('owner')
        )
        serializer = StorySerializer(
            instance=story,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(detail=True)
    def followers(self, request, slug=None):
        return self.get_followers_view(request, 'followers')

    @action(detail=True)
    def following(self, request, slug=None):
        return self.get_followers_view(request, 'following')

    @action(detail=True, methods=['post'])
    def follow(self, request, slug=None):
        """
        Is used for following another user.
        Creates recommendations, base on user's followers.
        If the user has been already followed to another user then
        cancel this following and delete user's followers from recommendations.
        """
        from_user = request.user
        to_user = self.get_object()
        response = follow_to_user(from_user, to_user)
        return Response({'status': response})

    @action(detail=True, methods=['post'])
    def block(self, request, slug=None):
        """
        Block the user and delete all connections between users.
        Otherwise, unblock the user.
        """
        from_user = request.user
        to_user = self.get_object()
        response = block_user(from_user, to_user)
        return Response({'status': response})

    @action(detail=True, methods=['post'])
    def report(self, request, slug=None):
        from_user = request.user
        to_user = self.get_object()
        serializer = serializers.ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(report_from=from_user, report_on=to_user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class RegisterConfirmAPIView(APIView):
    def get(self, request, uidb64, token):
        try:
            user, is_valid = check_token(uidb64, token)
            if not is_valid:
                return Response(
                    data={'status': 'Invalid token'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            else:
                ref = request.query_params.get('ref')
                if ref:
                    referrer = User.objects.get(referral_code=ref)
                    Referral.objects.create(referrer=referrer, referred_by=user)
                    send_mail(
                        subject='Congratulations',
                        message=f'{user.username} has registered using your link',
                        from_email=settings.EMAIL_HOST_USER,
                        recipient_list=[referrer.email],
                    )

                    # set vip with time duration
                    key = f'user:{referrer.id}:vip'
                    vip = redis_client.get(key)
                    if not vip:
                        redis_client.set(key, 60)
                    else:
                        redis_client.incrby(key, 60)
                user.is_active = True
                user.save()
                PeriodicTask.objects.get(name=f'delete-user-{user.id}').delete()
                return Response(
                    data={'status': 'User has been created'},
                    status=status.HTTP_201_CREATED,
                )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            return Response({'status': str(e)}, status.HTTP_400_BAD_REQUEST)


##############################################
# PASSWORD
class PasswordChangeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def put(self, request):
        serializer = serializers.PasswordSerializer(data=request.data)
        if serializer.is_valid():
            user = request.user
            user.set_password(serializer.validated_data['password'])
            user.save()
            return Response(
                data={'status': 'Changed'},
                status=status.HTTP_206_PARTIAL_CONTENT,
            )
        return Response(
            data={'status': "Isn't changed"},
            status=status.HTTP_400_BAD_REQUEST,
        )

    
class PasswordResetAPIView(APIView):
    def post(self, request):
        serializer = serializers.PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
        except User.DoesNotExist:
            return Response({'status': 'Not found'}, status.HTTP_404_NOT_FOUND)
        else:
            link = f'http://127.0.0.1:8000/api/password-reset-confirm'
            send_reset_email(user, link)
            return Response({'status': 'Check email'}, status.HTTP_200_OK)


class PasswordResetConfirmAPIView(APIView):
    def post(self, request, uidb64, token):
        serializer = serializers.PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user, is_valid = check_token(uidb64, token)
            if not is_valid:
                return Response(
                    data={'status': 'Invalid token'},
                    status=status.HTTP_400_BAD_REQUEST,
                )
            user.set_password(serializer.validated_data['new_password'])
            user.save()
            return Response(
                data={'status': 'Changed'},
                status=status.HTTP_206_PARTIAL_CONTENT,
            )
        except (TypeError, ValueError, OverflowError, User.DoesNotExist) as e:
            return Response({'status': str(e)}, status.HTTP_400_BAD_REQUEST)


##############################################
# FOLLOWERS
class AcceptFollowerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_slug):
        from_user = User.objects.get(slug=user_slug)
        to_user = request.user
        key = f'user:{to_user.id}:requests'
        request_exists = redis_client.smembers(key)
        if str(from_user.id) not in request_exists:
            msg = f'There is no request from {from_user.username}'
            return Response({'status': msg}, status.HTTP_404_NOT_FOUND)
        else:
            with transaction.atomic():
                Follower.objects.create(from_user=from_user, to_user=to_user)
                Action.objects.filter(
                    owner=from_user,
                    user=to_user,
                    act='wants to follow to you',
                ).delete()
            redis_client.srem(key, from_user.id)
            return Response({'status': 'Followed'}, status.HTTP_201_CREATED)


class RejectFollowerAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request, user_slug):
        from_user = User.objects.get(slug=user_slug)
        to_user = request.user
        key = f'user:{to_user.id}:requests'
        request_exists = redis_client.smembers(key)
        if str(from_user.id) not in request_exists:
            msg = f'There is no request from {from_user.username}'
            return Response({'status': msg}, status.HTTP_404_NOT_FOUND)
        else:
            Action.objects.filter(
                owner=from_user,
                user=to_user,
                act='wants to follow to you',
            ).delete()
            redis_client.srem(key, from_user.id)
            return Response({'status': 'Unfollowed'}, status.HTTP_204_NO_CONTENT)


##############################################
# OTHERS
class ReferralViewSet(ListModelViewSet):
    serializer_class = serializers.ReferralSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        referrals = (
            Referral.objects.filter(referrer=self.request.user).
            select_related('referrer', 'referred_by')
        )
        return referrals

    def list(self, request, *args, **kwargs):
        response = super().list(request, *args, **kwargs)
        response = {'result': response.data}
        code = request.user.referral_code
        response['code'] = code
        response['invite_link'] = f'http://localhost:8000/api/users/?ref={code}'
        return Response(response)


class SettingsAPIView(APIView):
    serializer_class = serializers.UserPrivacySerializer
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user.privacy
        serializer = self.serializer_class(user)
        return Response(serializer.data)

    def put(self, request, partial=False):
        user = request.user.privacy
        serializer = self.serializer_class(
            instance=user,
            data=request.data,
            partial=partial,
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()
        return Response(serializer.data, status.HTTP_206_PARTIAL_CONTENT)

    def patch(self, request):
        return self.put(request, partial=True)


class ActivityViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def list(self, request):
        user = self.request.user
        key = 'my_posts'
        posts = cache.get(key)
        if posts is None:
            posts = (
                Post.objects.annotated().
                exclude(archived=True).filter(likes=user)
            )
            cache.set(key, posts, 60 * 10)

        serializer = PostSerializer(
            instance=posts,
            many=True,
            context={'request': request},
        )

        key = 'my_comments'
        comments = cache.get(key)
        if comments is None:
            comments = (
                user.comments.exclude(post__archived=True).
                select_related('post', 'owner')
            )
            cache.set(key, comments, 60 * 10)

        comments_serializer = CommentSerializer(
            instance=comments,
            many=True,
            context={'request': request},
            exclude=['text', 'owner', 'replies'],
        )
        response_data = {}
        response_data['liked_posts'] = serializer.data
        response_data['comments'] = comments_serializer.data
        return Response(response_data)


class ActionViewSet(mixins.DestroyModelMixin,
                    mixins.ListModelMixin,
                    GenericViewSet):
    serializer_class = serializers.ActionSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        user = self.request.user
        actions = (
            Action.objects.filter(Q(post__owner=user) | Q(user=user)).
            select_related('owner', 'content_type')
        )
        return actions


class SavedPostsViewSet(ListModelViewSet):
    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_queryset('saved_posts'))
    def get_queryset(self): 
        user = self.request.user
        posts = (
            Post.objects.annotated().
            exclude(archived=True).filter(saved=user)
        )
        return posts


class BlockedUsersViewSet(ListModelViewSet):
    serializer_class = serializers.UserSerializer
    permission_classes = [IsAuthenticated]

    @method_decorator(cache_queryset('blocked'))
    def get_queryset(self):
        user = self.request.user
        blocked = User.objects.blocked(user=user)
        return blocked


class RecommendationViewSet(ListModelViewSet):
    serializer_class = serializers.UserSerializer
    permission_classes = [IsAuthenticated]
    
    def get_queryset(self):
        r = Recommender()
        recommendations = r.suggests_for_user(self.request.user)
        return recommendations


class VipAPIView(APIView):
    @staticmethod
    def get_key(request):
        user = request.user
        key = f'user:{user.id}:vip'
        vip = redis_client.get(key)
        return vip

    def get(self, request, *args, **kwargs):
        vip_duration = self.get_key(request)
        if not vip_duration:
            message = (
                "You don't have vip status. "
                "Invite friends and retrieve free vip status."
            )
            return Response({'status': message})
        else:
            return Response({'duration': vip_duration})

    def post(self, request, *args, **kwargs):
        user = request.user
        vip_duration = self.get_key(request)
        if vip_duration is None:
            return Response({'status': 'Error'}, status.HTTP_400_BAD_REQUEST)

        # process data
        serializer = serializers.VipSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        active_key = 'active_vip_users'
        is_activated = redis_client.sismember(active_key, user.id)
        if is_activated:
            return Response({'status': 'Wait until the current vip status ends'})

        # add the user to vip users
        duration = serializer.validated_data['duration']
        vip_duration = int(vip_duration)
        if vip_duration < duration or vip_duration == 0:
            return Response({'status': 'Error'})

        difference = vip_duration - duration
        key = f'user:{user.id}:vip'
        redis_client.set(key, difference)
        redis_client.sadd(active_key, user.id)

        # schedule the task
        # remove the user from VIP users after the end of the VIP status
        timestamp = datetime.now() + timedelta(minutes=duration)
        crontab, _ = CrontabSchedule.objects.get_or_create(
            minute=timestamp.minute,
            hour=timestamp.hour,
            day_of_month=timestamp.day,
            month_of_year=timestamp.month,
        )
        PeriodicTask.objects.create(
            crontab=crontab,
            name=f'cancel-vip-for-{user.id}-{int(timestamp.timestamp())}',
            task='users.tasks.cancel_vip',
            args=json.dumps([user.id]),
            one_off=True,
        )
        return Response({'status': "Well done, you've activated vip status"})
