from django.db.models import Count
from django.core.cache import cache
from django.conf import settings

from django_filters.rest_framework import DjangoFilterBackend

from rest_framework.filters import OrderingFilter
from rest_framework.viewsets import ModelViewSet
from rest_framework.decorators import action
from rest_framework.views import Response
from rest_framework.permissions import (
    IsAuthenticated,
    IsAuthenticatedOrReadOnly,
)
from rest_framework import parsers, status, mixins, viewsets

from users.utils import create_action
from users.tasks import check_story

from .serializers import *
from .permissions import IsOwner


###############################################################################


class PostViewSet(ModelViewSet):
    queryset = Post.objects.all().select_related("owner").prefetch_related("tags")
    serializer_class = PostListSerializer
    detail_serializer_class = PostDetailSerializer
    permission_classes = [IsAuthenticatedOrReadOnly, IsOwner]
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser]
    filter_backends = [DjangoFilterBackend, OrderingFilter]
    filterset_fields = ["owner"]
    ordering_fields = ["date"]

    def get_serializer_class(self):
        if self.action in ["list", "create"]:
            return self.serializer_class
        return self.detail_serializer_class

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(
            data=request.data, context={"request": request}
        )
        if serializer.is_valid():
            serializer.save(owner=self.request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def list(self, request, *args, **kwargs):
        queryset = self.filter_queryset(self.get_queryset())
        response = super().list(request, *args, **kwargs)
        response_data = {"result": response.data}

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

        comments = instance.comments.all().select_related("owner")
        serializer = CommentSerializer(comments, many=True)

        response_data = response.data
        response_data["comments"] = serializer.data
        return Response(response_data)

    @action(detail=True, methods=["post"])
    def comment(self, request, pk=None):
        p_id = self.get_object()
        com = CommentSerializer(data=request.data)
        if com.is_valid():
            Comment.objects.create(
                owner=self.request.user, post=p_id, text=com.validated_data["text"]
            )
            return Response(com.data)
        return Response(com.errors)

    @action(detail=True, methods=["post"])
    def liked(self, request, pk=None):
        p = self.get_object()
        if p.is_like.filter(id=request.user.id).exists():
            p.is_like.remove(request.user)
            msg = "unliked"
        else:
            p.is_like.add(request.user)
            msg = "liked"
            create_action(request.user, "liked post", p.photo, p.owner)
        p.save()
        return Response({"message": msg})


class StoryViewSet(
    mixins.CreateModelMixin,
    mixins.RetrieveModelMixin,
    mixins.DestroyModelMixin,
    mixins.ListModelMixin,
    viewsets.GenericViewSet,
):
    queryset = Story.objects.all().select_related("owner")
    serializer_class = StorySerializer
    parser_classes = [parsers.JSONParser, parsers.MultiPartParser]
    permission_classes = [IsAuthenticated, IsOwner]

    def retrieve(self, request, *args, **kwargs):
        check_story.delay()
        return super().retrieve(request, *args, **kwargs)

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if serializer.is_valid():
            serializer.save(owner=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
