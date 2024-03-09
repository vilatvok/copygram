from rest_framework import serializers
from rest_framework.fields import empty

from taggit.serializers import TaggitSerializer, TagListSerializerField
from taggit.models import Tag

from common.utils import set_serializer_fields

from mainsite.models import Post, Comment, PostMedia, Story


class CommentSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(source='owner.username')

    class Meta:
        model = Comment
        fields = ['owner', 'text', 'date']
                

class BasePostSerializer(TaggitSerializer, serializers.HyperlinkedModelSerializer):
    owner = serializers.StringRelatedField(source='owner.username')
    total_likes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        exclude = ['is_comment', 'is_like']


class PostMediaSerializer(serializers.Serializer):
    file = serializers.FileField(allow_empty_file=False, use_url=False)


class PostListSerializer(BasePostSerializer):
    tags = TagListSerializerField(
        write_only=True,
        child=serializers.CharField(allow_blank=True)
    )
    file = serializers.CharField(read_only=True)
    files = serializers.ListField(
        child=serializers.FileField(allow_empty_file=False, use_url=False),
        write_only=True
    )

    def create(self, validated_data):
        """Lists are not currently supported in HTML input."""
        files = validated_data.pop("files")
        post = Post.objects.create(**validated_data)
        files_list = []
        for file in files:
            files_list.append(PostMedia(post=post, file=file))
        PostMedia.objects.bulk_create(files_list)
        return post


class PostDetailSerializer(BasePostSerializer):
    tags = TagListSerializerField(child=serializers.CharField(allow_blank=True))


class StorySerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(source='owner.username')

    class Meta:
        model = Story
        fields = '__all__'


class TagSerializer(serializers.HyperlinkedModelSerializer):
    posts = serializers.SerializerMethodField()

    class Meta:
        model = Tag
        fields = ['url', 'name', 'posts']

    def __init__(self, instance=None, data=empty, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(instance, data, **kwargs)
        if fields:
            set_serializer_fields(fields, self.fields)

    def get_posts(self, obj):
        queryset = (
            Post.objects.filter(tags__name__in=[obj.name]).
            select_related('owner').prefetch_related('tags')
        )
        serializer = PostListSerializer(queryset, many=True, context=self.context)
        return serializer.data