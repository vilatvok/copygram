from django.db import transaction
from django.db.models import Q
from django.contrib.auth import get_user_model
from django.utils.http import urlsafe_base64_decode
from django.utils.encoding import force_str
from django.utils.decorators import method_decorator
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.contrib.auth.tokens import default_token_generator

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework import status, filters, mixins
from rest_framework.views import APIView
from rest_framework.viewsets import ViewSet, ModelViewSet, GenericViewSet
from rest_framework.response import Response
from rest_framework.decorators import action
from rest_framework.pagination import PageNumberPagination

from common.utils import redis_client, get_blocked_users

from users.serializers import (
    ActionSerializer,
    PasswordResetConfirmSerializer,
    PasswordResetSerializer,
    ReportSerializer,
    UserCreateSerializer,
    UserPrivacySerializer,
    UserSerializer,
    PasswordSerializer,
    UserUpdateSerializer,
)
from users.permissions import IsOwner
from users.models import Action, Follower
from users.utils import (
    Recommender,
    block_user,
    follow_to_user,
    get_user_posts,
    send_reset_email,
)

from blogs.models import Post, Story
from blogs.serializers import (
    PostSerializer,
    StorySerializer,
    CommentSerializer,
)


User = get_user_model()


class UserPagination(PageNumberPagination):
    page_size = 10
    page_size_query_param = 'page_size'
    max_page_size = 100


class UserViewSet(ModelViewSet):
    lookup_field = 'slug'
    permission_classes = [IsOwner]
    pagination_class = UserPagination
    filter_backends = [DjangoFilterBackend, filters.SearchFilter]
    filterset_fields = ['username']
    search_fields = ['username']

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

        serializer = UserSerializer(
            instance=queryset,
            many=True,
            context={'request': request},
            exclude=['phone', 'last_login'],
        )
        return Response(serializer.data)

    def get_serializer_class(self):
        if self.action in ['create']:
            return UserCreateSerializer
        elif self.action in ['update', 'partial_update']:
            return UserUpdateSerializer
        return UserSerializer

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
        response = block_user(request, from_user, to_user)
        return Response({'status': response})

    @action(detail=True, methods=['post'])
    def report(self, request, slug=None):
        from_user = request.user
        to_user = self.get_object()
        serializer = ReportSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(report_from=from_user, report_on=to_user)
        return Response(serializer.data, status.HTTP_201_CREATED)


class SettingsAPIView(APIView):
    def get(self, request):
        user = request.user.privacy
        serializer = UserPrivacySerializer(user)
        return Response(serializer.data)

    def put(self, request, partial=False):
        user = request.user.privacy
        serializer = UserPrivacySerializer(
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


class ActionViewSet(
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = ActionSerializer

    def get_queryset(self):
        user = self.request.user
        actions = (
            Action.objects.filter(Q(post__owner=user) | Q(user=user)).
            select_related('owner', 'content_type')
        )
        return actions


class SavedPostsViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = PostSerializer

    def get_queryset(self):
        user = self.request.user
        posts = (
            Post.objects.annotated().
            exclude(archived=True).filter(saved=user)
        )
        return posts

    def list(self, request, *args, **kwargs):
        key = 'saved_posts'
        posts = cache.get(key)
        if posts is None:
            posts = self.get_queryset()
            cache.set(key, posts)

        serializer = self.get_serializer(instance=posts, many=True)
        return Response(serializer.data)


class BlockedUsersViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = UserSerializer

    def get_queryset(self):
        user = self.request.user
        queryset = User.objects.blocked(user=user)
        return queryset

    @method_decorator(cache_page(60 * 60))
    def list(self, request):
        blocked = self.get_queryset()
        serializer = self.get_serializer(blocked, many=True)
        return Response(serializer.data)


class RecommendationViewSet(
    mixins.ListModelMixin,
    GenericViewSet,
):
    serializer_class = UserSerializer

    def get_queryset(self):
        r = Recommender()
        recommendations = r.suggests_for_user(self.request.user)
        return recommendations
    
    def list(self, request):
        key = 'recommendations'
        recommendations = cache.get(key)
        if recommendations is None:
            recommendations = self.get_queryset()
            cache.set(key, recommendations)

        serializer = self.get_serializer(recommendations, many=True)
        return Response(serializer.data)


class AcceptFollowerAPIView(APIView):
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
    def post(self, request, user_slug):
        from_user = User.objects.get(slug=user_slug)
        to_user = request.user
        key = f'user:{to_user.id}:requests'
        request_exists = redis_client.smembers(key)
        if str(from_user.id) not in request_exists:
            msg = f'There is no request from {from_user.username}'
            return Response({'status': msg}, status.HTTP_404_NOT_FOUND)
        Action.objects.filter(
            owner=from_user,
            user=to_user,
            act='wants to follow to you',
        ).delete()
        redis_client.srem(key, from_user.id)
        return Response({'status': 'Unfollowed'}, status.HTTP_204_NO_CONTENT)


class PasswordChangeAPIView(APIView):
    def put(self, request):
        serializer = PasswordSerializer(data=request.data)
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
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        try:
            user = User.objects.get(email=serializer.validated_data['email'])
        except User.DoesNotExist:
            return Response({'status': 'Not found'}, status.HTTP_404_NOT_FOUND)
        else:
            link = f'http://127.0.0.1:8000/api/password-reset-confirm',
            send_reset_email(user, link)
            return Response({'status': 'Check email'}, status.HTTP_200_OK)


class PasswordResetConfirmAPIView(APIView):
    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        decoded_user = force_str(urlsafe_base64_decode(uidb64))
        user = User.objects.get(username=decoded_user)
        valid = default_token_generator.check_token(user, token)
        if not valid:
            return Response(
                data={'status': 'Invalid token'},
                status=status.HTTP_400_BAD_REQUEST,
            )
        user.set_password(serializer.validated_data['new_password'])
        user.save()
        return Response({'status': 'Changed'}, status.HTTP_206_PARTIAL_CONTENT)
