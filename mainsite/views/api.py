from django.db.models import Count
from django.core.cache import cache
from django.conf import settings

from rest_framework import parsers, status, mixins, viewsets
from rest_framework.viewsets import ModelViewSet, ReadOnlyModelViewSet
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, IsAuthenticatedOrReadOnly

from taggit.models import Tag

from mainsite.models import Post, Comment, PostMedia, Story
from mainsite.serializers import (
    CommentSerializer, 
    PostDetailSerializer, 
    PostListSerializer, 
    StorySerializer,
    TagSerializer,
    PostMediaSerializer,
)
from mainsite.permissions.api import IsOwner
from mainsite.tasks import delete_story_scheduler

from common.utils import create_action, get_posts


class PostViewSet(ModelViewSet):
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwner]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser]

    def get_queryset(self):
        queryset = get_posts(blocked=self.request.session.get('blocked', []))
        return queryset
    
    def get_serializer_class(self):
        if self.action in ['list', 'create']:
            return PostListSerializer
        return PostDetailSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, 
            context={'request': request}
        )
        serializer.is_valid(raise_exception=True)
        files = serializer.validated_data['files']
        serializer.save(owner=self.request.user)
        for file in files:
            PostMedia.objects.create(post=serializer.instance, file=file)
        return Response(serializer.data, status.HTTP_201_CREATED)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        
        response = super().list(request, *args, **kwargs)
        response_data = {'result': response.data}

        # Set redis cache for showing posts count
        redis_cache = cache.get(settings.TOTAL)
        if redis_cache:
            total_posts = redis_cache
        else:
            total_posts = queryset.aggregate(total=Count('id')).get('total')
            cache.set(settings.TOTAL, total_posts, 60)

        response.data = response_data
        response_data['total_posts'] = total_posts
        return response

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        response = self.get_serializer(instance)

        files = instance.files.all()
        file_serializer = PostMediaSerializer(files, many=True)

        comments = instance.comments.all().select_related('owner')
        comment_serializer = CommentSerializer(comments, many=True)

        response_data = response.data
        response_data['comments'] = comment_serializer.data
        response_data['media'] = file_serializer.data
        return Response(response_data)

    @action(detail=True, methods=['post'])
    def add_comment(self, request, pk=None):
        com = CommentSerializer(data=request.data)
        com.is_valid(raise_exception=True)
        post = self.get_object()
        file = post.files.first()
        user = request.user
        Comment.objects.create(
            owner=user, post=post, text=com.validated_data['text']
        )
        if user != post.owner:
            create_action(user, 'comment on', file.file, post)
        return Response(com.data)

    @action(detail=True,
            methods=['delete'],
            url_path='delete_comment/(?P<comment_id>[^/.]+)')
    def delete_comment(self, request, comment_id, pk=None):
        Comment.objects.get(id=comment_id).delete()
        return Response({'status': 'deleted'}, status.HTTP_204_NO_CONTENT)

    @action(detail=True, methods=['post'])
    def liked(self, request, pk=None):
        post = self.get_object()
        file = post.files.first()
        user = request.user
        if post.is_like.filter(id=user.id).exists():
            post.is_like.remove(user)
            msg = 'unliked'
        else:
            post.is_like.add(user)
            msg = 'liked'
            if user != post.owner:
                create_action(user, 'liked post', file.file, post)
        post.save()
        return Response({'status': msg})


class TagViewSet(ReadOnlyModelViewSet):
    queryset = Tag.objects.all()
    serializer_class = TagSerializer

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())

        page = self.paginate_queryset(queryset)
        if page is not None:
            serializer = self.get_serializer(page, many=True, fields=('url', 'name'))
            return self.get_paginated_response(serializer.data)

        serializer = self.get_serializer(queryset, many=True, fields=('url', 'name'))
        return Response(serializer.data)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, fields=('name', 'posts'))
        return Response(serializer.data)
    

class StoryViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    serializer_class = StorySerializer
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser]
    permission_classes = [IsAuthenticated, IsOwner]

    def get_queryset(self):
        return (
            Story.objects.exclude(owner__in=self.request.session['blocked']).
            select_related('owner')
        )

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        serializer.save(owner=request.user)
        delete_story_scheduler(serializer.instance.id, serializer.instance.date)
        return Response(serializer.data, status.HTTP_201_CREATED)
