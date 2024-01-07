from rest_framework import serializers

from .models import Post, Comment, Story

from taggit.serializers import TaggitSerializer, TagListSerializerField


class CommentSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(source="owner.username")

    class Meta:
        model = Comment
        fields = ["owner", "text", "date"]


class PostListSerializer(TaggitSerializer, serializers.HyperlinkedModelSerializer):
    owner = serializers.StringRelatedField(source="owner.username")
    total_likes = serializers.IntegerField(read_only=True)
    tags = TagListSerializerField(write_only=True)

    class Meta:
        model = Post
        exclude = ("is_like", "is_comment")


class PostDetailSerializer(PostListSerializer):
    photo = serializers.ImageField(read_only=True)
    tags = TagListSerializerField()


class StorySerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(source="owner.username")

    class Meta:
        model = Story
        fields = "__all__"
