from django.conf import settings
from django.db import transaction
from django.db.models import Count
from django.core.cache import cache

from rest_framework import status, mixins, viewsets
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)

from taggit.models import Tag

from blogs.models import Comment, Story
from blogs.serializers import (
    CommentSerializer,
    PostDetailSerializer,
    PostListSerializer,
    StorySerializer,
    TagSerializer,
    PostMediaSerializer,
)
from blogs.permissions import IsOwner
from blogs.tasks import delete_story_scheduler

from common.utils import create_action, get_posts
from blogs.utils import like_post, save_post
from users.models import Follower


class PostViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwner]

    def get_queryset(self):
        blocked = self.request.session.get('blocked', [])
        queryset = get_posts(blocked=blocked)
        return queryset

    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return PostListSerializer
        return PostDetailSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        response = super().list(request, *args, **kwargs)
        response_data = {'posts': response.data}

        # Set redis cache for showing posts count
        redis_cache = cache.get(settings.TOTAL)
        if redis_cache:
            total_posts = redis_cache
        else:
            total_posts = queryset.aggregate(total=Count('id')).get('total')
            cache.set(settings.TOTAL, total_posts, 60)

        response_data['total_posts'] = total_posts
        return Response(response_data)

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        response = self.get_serializer(post)

        files = post.files.all()
        file_serializer = PostMediaSerializer(files, many=True)

        comments = post.comments.all().select_related('owner')
        comment_serializer = CommentSerializer(
            instance=comments,
            many=True,
            context={'request': request},
            fields=['post'],
        )
        comment_data = comment_serializer.data

        response_data = response.data
        response_data['media'] = file_serializer.data

        owner_privacy = post.owner.privacy
        is_follower = Follower.objects.filter(
            from_user=request.user,
            to_user=post.owner,
        )

        if owner_privacy.comments == 'followers' and is_follower:
            response_data['comments'] = comment_data
        else:
            response_data['comments'] = comment_data

        return Response(response_data)

    @action(detail=True, methods=['post'], url_path='comment')
    def add_comment(self, request, pk=None):
        user = request.user
        post = self.get_object()
        first_image = post.files.first()
        comment = CommentSerializer(data=request.data)
        comment.is_valid(raise_exception=True)
        with transaction.atomic():
            comment.save(owner=user, post=post)
            if user != post.owner:
                create_action(user, 'commented on', post, first_image.file)
        return Response(comment.data)

    @action(
        detail=True,
        methods=['delete'],
        url_path='delete-comment/(?P<comment_id>[^/.]+)',
    )
    def delete_comment(self, request, comment_id, pk=None):
        Comment.objects.get(id=comment_id).delete()
        return Response({'status': 'deleted'}, status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='like')
    def add_like(self, request, pk=None):
        user = request.user
        post = self.get_object()
        response = like_post(user, post)
        return Response({'status': response})

    @action(detail=True, methods=['post'], url_path='save')
    def _save_post(self, request, pk=None):
        user = request.user
        post = self.get_object()
        response = save_post(user, post)
        return Response({'status': response})


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(
            instance=queryset,
            many=True,
            fields=['name', 'posts'],
        )
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, fields=['url'])
        return Response(serializer.data)


class StoryViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return (
            Story.objects.select_related('owner').
            exclude(owner__in=self.request.session['blocked'])
        )

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)
        delete_story_scheduler(
            serializer.instance.id,
            serializer.instance.date,
        )
