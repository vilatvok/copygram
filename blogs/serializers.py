from django.db import transaction

from rest_framework import serializers

from taggit.models import Tag
from taggit.serializers import TaggitSerializer, TagListSerializerField

from common.utils import CustomSerializer

from blogs.models import Post, Comment, PostMedia, Story


class CommentSerializer(CustomSerializer, serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    post = serializers.HyperlinkedRelatedField(
        view_name='post-detail',
        read_only=True,
    )

    class Meta:
        model = Comment
        fields = ['owner', 'post', 'text', 'date']


class PostMediaSerializer(serializers.Serializer):
    file = serializers.FileField(allow_empty_file=False, use_url=False)


class BasePostSerializer(
    TaggitSerializer,
    serializers.HyperlinkedModelSerializer,
):
    owner = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_url_kwarg='slug',
        read_only=True,
    )
    class Meta:
        model = Post
        exclude = ['is_comment', 'saved']


class PostListSerializer(BasePostSerializer):
    tags = TagListSerializerField(
        write_only=True,
        child=serializers.CharField(allow_blank=True),
    )
    file = serializers.CharField(read_only=True)
    files = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False, use_url=False),
        write_only=True,
    )

    @transaction.atomic
    def create(self, validated_data):
        """Lists are not currently supported in HTML input."""
        files = validated_data.pop('files')
        post = Post.objects.create(**validated_data)
        files_list = []
        for file in files:
            files_list.append(PostMedia(post=post, file=file))
        PostMedia.objects.bulk_create(files_list)
        return post


class PostDetailSerializer(BasePostSerializer):
    tags = TagListSerializerField(
        child=serializers.CharField(allow_blank=True),
    )
    likes = serializers.IntegerField(read_only=True, source='likes_count')


class StorySerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.StringRelatedField(source='owner.username')

    class Meta:
        model = Story
        fields = ['url', 'owner', 'img', 'date']


class TagSerializer(CustomSerializer, serializers.HyperlinkedModelSerializer):
    posts = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['url', 'name', 'posts']

    def get_posts(self, obj):
        queryset = (
            Post.objects.filter(tags__name__in=[obj.name]).
            select_related('owner').prefetch_related('tags')
        )
        serializer = PostListSerializer(
            instance=queryset,
            many=True,
            context=self.context,
        )
        return serializer.data
