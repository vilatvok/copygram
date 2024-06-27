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
    likes = serializers.IntegerField(read_only=True, source='likes_count')
    replies = serializers.SerializerMethodField()

    class Meta:
        model = Comment
        fields = [
            'id',
            'owner',
            'post',
            'text',
            'date',
            'parent',
            'likes',
            'replies',
        ]

    def get_replies(self, obj):
        replies = obj.descendants().select_related('owner', 'parent')
        serializer = CommentSerializer(
            instance=replies,
            many=True,
            context=self.context,
            exclude=['post']
        )
        return serializer.data

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        if representation['parent'] is None:
            representation.pop('parent')
        return representation


class BasePostSerializer(
    TaggitSerializer,
    CustomSerializer,
    serializers.HyperlinkedModelSerializer,
):
    owner = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_field='slug',
        read_only=True,
    )


class PostMediaSerializer(serializers.Serializer):
    file = serializers.FileField(allow_empty_file=False, use_url=False)


class PostSerializer(BasePostSerializer):
    tags = TagListSerializerField(
        write_only=True,
        child=serializers.CharField(allow_blank=True),
    )
    file = serializers.CharField(read_only=True)
    files = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False, use_url=False),
        write_only=True,
    )

    class Meta:
        model = Post
        exclude = ['is_comment', 'likes', 'saved', 'archived']
        extra_kwargs = {'description': {'write_only': True}}

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


class PostUpdateSerializer(BasePostSerializer):
    tags = TagListSerializerField(child=serializers.CharField(allow_blank=True))
    likes = serializers.IntegerField(read_only=True, source='likes_count')
    
    class Meta:
        model = Post
        exclude = ['is_comment', 'saved', 'archived']


class PostDetailSerializer(PostUpdateSerializer):
    files = PostMediaSerializer(
        many=True,
        read_only=True,
        source='get_files',
    )
    comments = serializers.SerializerMethodField()

    def get_comments(self, obj):
        comments = (
            obj.comments.with_likes().
            filter(parent=None).
            select_related('owner', 'parent')
        )
        serializer = CommentSerializer(
            instance=comments,
            many=True,
            read_only=True,
            exclude=['post'],
        )
        return serializer.data


class ArchivePostsSerializer(PostSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='archive-get-post',
        read_only=True,
    )


class ArchivePostSerializer(PostDetailSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='archive-get-post',
        read_only=True,
    )


class StorySerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.HyperlinkedRelatedField(
        view_name='user-detail',
        lookup_field='slug',
        read_only=True,
    )

    class Meta:
        model = Story
        fields = ['url', 'owner', 'img', 'date']


class ArchiveStorySerializer(StorySerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='archive-story',
        read_only=True,
    )


class TagSerializer(CustomSerializer, serializers.HyperlinkedModelSerializer):
    posts = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['url', 'name', 'posts']

    def get_posts(self, obj):
        queryset = (
            Post.objects.annotated().
            filter(tags__name__in=[obj.name]).
            exclude(archived=True)
        )
        serializer = PostSerializer(
            instance=queryset,
            many=True,
            context=self.context,
        )
        return serializer.data
