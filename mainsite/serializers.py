from rest_framework import serializers
from rest_framework.fields import empty

from taggit.serializers import TaggitSerializer, TagListSerializerField
from taggit.models import Tag

from common.utils import set_serializer_fields

from mainsite.models import Post, Comment, Story


class CommentSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(source='owner.username')

    class Meta:
        model = Comment
        fields = ['owner', 'text', 'date']

    def __init__(self, instance=None, data=empty, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(instance, data, **kwargs)
        
        if fields:
            set_serializer_fields(fields, self.fields)
                

class BasePostSerializer(TaggitSerializer, serializers.HyperlinkedModelSerializer):
    owner = serializers.StringRelatedField(source='owner.username')
    total_likes = serializers.IntegerField(read_only=True)

    class Meta:
        model = Post
        exclude = ['is_comment', 'is_like']


class PostMediaSerializer(serializers.Serializer):
    file = serializers.FileField()


class PostListSerializer(BasePostSerializer):
    tags = TagListSerializerField(
        write_only=True,
        child=serializers.CharField(allow_blank=True)
    )
    file = serializers.CharField(read_only=True)
    files = PostMediaSerializer(write_only=True, many=True)


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
            allowed = set(fields)
            old = set(self.fields)
            for field in old - allowed:
                self.fields.pop(field)

    def get_posts(self, obj):
        queryset = (
            Post.objects.filter(tags__name__in=[obj.name]).
            select_related('owner').prefetch_related('tags')
        )
        serializer = PostListSerializer(queryset, many=True, context=self.context)
        return serializer.data