from django.db import transaction
from django.db.models import Q
from django.core.cache import cache
from django.contrib.contenttypes.models import ContentType

from rest_framework import status
from rest_framework.viewsets import (
    ViewSet,
    ModelViewSet,
    ReadOnlyModelViewSet,
)
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)

from taggit.models import Tag

from blogs import utils
from blogs.models import Comment, Story
from blogs.serializers import (
    ArchivePostSerializer,
    ArchivePostsSerializer,
    ArchiveStorySerializer,
    CommentSerializer,
    PostSerializer,
    PostUpdateSerializer,
    PostDetailSerializer,
    StorySerializer,
    TagSerializer,
)
from blogs.permissions import IsOwner

from common.utils import (
    NonUpdateViewSet,
    create_action,
    get_blocked_users,
)

from users.models import Archive, Follower


class PostViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwner]

    def get_queryset(self):
        key = 'posts'
        queryset = cache.get(key)
        if queryset is None:
            queryset = utils.get_posts()
            cache.set(key, queryset, 60 * 5)
        return queryset

    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return PostSerializer
        elif self.action in ['update', 'partial_update']:
            return PostUpdateSerializer
        return PostDetailSerializer

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        post = self.get_object()
        owner_privacy = post.owner.privacy
        excluded = []
        if post.owner != request.user:
            is_follower = Follower.objects.filter(
                from_user=request.user,
                to_user=post.owner,
            ).exists()

            # check if user hid comments
            if owner_privacy.comments == 'followers' and not is_follower:
                excluded.append('comments')

            # check if user hid likes count
            if owner_privacy.likes == 'followers' and not is_follower:
                excluded.append('likes')
            elif owner_privacy.likes == 'nobody':
                excluded.append('likes')

        serializer = self.get_serializer(
            instance=post,
            exclude=excluded,
        )
        return Response(serializer.data)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        post = self.get_object()
        target_ct = ContentType.objects.get_for_model(post)
        post.archived = True
        with transaction.atomic():
            post.save()
            Archive.objects.create(content_type=target_ct, object_id=post.id)
        return Response({'status': 'Archived'}, status.HTTP_206_PARTIAL_CONTENT)

    @action(detail=True, methods=['post'], url_path='comment')
    def add_comment(self, request, pk=None):
        user = request.user
        post = self.get_object()
        comment = CommentSerializer(
            data=request.data,
            context={'request': request},
        )
        comment.is_valid(raise_exception=True)
        with transaction.atomic():
            comment.save(owner=user, post=post)
            if user != post.owner:
                create_action(user, 'commented on', post, post.file)
        return Response(comment.data)
    
    @action(
        detail=True,
        methods=['post'],
        url_path='reply-to-comment/(?P<comment_id>[^/.]+)',
    )
    def reply_to_comment(self, request, comment_id, pk=None):
        user = request.user
        post = self.get_object()
        comment_serializer = CommentSerializer(
            data=request.data,
            context={'request': request},
        )
        comment_serializer.is_valid(raise_exception=True)
        with transaction.atomic():
            comment = Comment.objects.filter(id=comment_id, post=post)
            if comment.exists():
                comment_serializer.save(owner=user, post=post, parent=comment[0])
                if user != post.owner:
                    create_action(user, 'replied to comment', post, post.file)
            else:
                return Response(
                    data={'status': 'Comment not found'},
                    status=status.HTTP_404_NOT_FOUND,
                )
        return Response(comment_serializer.data)

    @action(
        detail=True,
        methods=['post'],
        url_path='like-comment/(?P<comment_id>[^/.]+)',
    )
    def like_comment(self, request, comment_id, pk=None):
        user = request.user
        post = self.get_object()
        comment = Comment.objects.filter(id=comment_id, post=post)
        if comment.exists():
            comment = comment[0]
            if comment.likes.filter(id=user.id).exists():
                comment.likes.remove(user)
                state = 'Unliked'
            else:
                with transaction.atomic():
                    comment.likes.add(user)
                    if user != post.owner:
                        create_action(user, 'liked comment', post, post.file)
                state = 'Liked'
            return Response({'status': state}, status.HTTP_201_CREATED)
        else:
            return Response(
                data={'status': 'Comment not found'},
                status=status.HTTP_404_NOT_FOUND,
            )
    
    @action(
        detail=True,
        methods=['delete'],
        url_path='delete-comment/(?P<comment_id>[^/.]+)',
    )
    def delete_comment(self, request, comment_id, pk=None):
        post = self.get_object()
        comment = Comment.objects.get(id=comment_id)
        if comment.owner != request.user and post.owner != request.user:
            return Response({'status': 'You cant delete this comment'})
        comment.delete()
        return Response({'status': 'deleted'}, status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'], url_path='like')
    def add_like(self, request, pk=None):
        user = request.user
        post = self.get_object()
        response = utils.like_post(user, post)
        return Response({'status': response}, status.HTTP_201_CREATED)

    @action(detail=True, methods=['post'], url_path='save')
    def save_post(self, request, pk=None):
        user = request.user
        post = self.get_object()
        response = utils.save_post(user, post)
        return Response({'status': response}, status.HTTP_201_CREATED)


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def list(self, request):
        queryset = self.filter_queryset(self.get_queryset())
        serializer = self.get_serializer(
            instance=queryset,
            many=True,
            exclude=['name', 'posts'],
        )
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, exclude=['url'])
        return Response(serializer.data)


class StoryViewSet(NonUpdateViewSet):
    serializer_class = StorySerializer
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        key = 'stories'
        stories = cache.get(key)
        if stories is None:
            blocked_users = get_blocked_users(self.request.user)
            stories = Story.objects.exclude(
                Q(owner__in=blocked_users) |
                Q(archived=True),
            ).select_related('owner')
            cache.set(key, stories, 60 * 3)
        return stories

    def perform_create(self, serializer):
        serializer.save(owner=self.request.user)

    @action(detail=True, methods=['post'])
    def archive(self, request, pk=None):
        story = self.get_object()
        target_ct = ContentType.objects.get_for_model(story)
        story.archived = True
        with transaction.atomic():
            story.save()
            Archive.objects.create(content_type=target_ct, object_id=story.id)
        return Response({'status': 'Archived'}, status.HTTP_206_PARTIAL_CONTENT)


class ArchiveViewSet(ViewSet):
    permission_classes = [IsAuthenticated]

    def get_posts_queryset(self):
        return utils.get_archived_posts(self.request.user)

    def get_stories_queryset(self):
        return utils.get_archived_stories(self.request.user)

    @action(detail=False)
    def posts(self, request, pk=None):
        posts = self.get_posts_queryset()
        serializer = ArchivePostsSerializer(
            instance=posts,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)

    @action(detail=False)
    def stories(self, request, pk=None):
        stories = self.get_stories_queryset()
        serializer = ArchiveStorySerializer(
            instance=stories,
            many=True,
            context={'request': request},
        )
        return Response(serializer.data)
    
    @action(
        detail=False,
        methods=['get', 'delete', 'post'],
        url_path='posts/(?P<pk>[^/.]+)',
    )
    def get_post(self, request, pk=None):
        post = self.get_posts_queryset().get(pk=pk)
        if request.method == 'GET':
            serializer = ArchivePostSerializer(
                instance=post,
                context={'request': request},
            ) 
            return Response(serializer.data)
        elif request.method == 'POST':
            post.archived = False
            with transaction.atomic():
                post.save()
                Archive.objects.get(post=post).delete()
        elif request.method == 'DELETE':
            post.delete()
            return Response({'status': 'Deleted'}, status.HTTP_204_NO_CONTENT)
    
    @action(
        detail=False,
        methods=['get', 'delete', 'post'],
        url_path='stories/(?P<pk>[^/.]+)',
    )
    def story(self, request, pk=None):
        story = self.get_stories_queryset().get(pk=pk)
        if request.method == 'GET':
            serializer = ArchiveStorySerializer(
                instance=story,
                context={'request': request},
            )
            return Response(serializer.data)
        elif request.method == 'POST':
            story.archived = False
            with transaction.atomic():
                story.save()
                Archive.objects.get(story=story).delete()
            return Response({'status': 'Restored'}, status.HTTP_204_NO_CONTENT)
        elif request.method == 'DELETE':
            story.delete()
            return Response({'status': 'Deleted'}, status.HTTP_204_NO_CONTENT)
