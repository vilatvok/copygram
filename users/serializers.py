from django.contrib.auth import get_user_model
from django.contrib.auth.models import User

from rest_framework import serializers

from .models import *


class UserSerializer(serializers.HyperlinkedModelSerializer):
    class Meta:
        model = get_user_model()
        fields = ["url", "id", "username", "phone"]

        
class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)


class ActionSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(source="owner.username")
    target = serializers.StringRelatedField()

    class Meta:
        model = Action
        exclude = ["ti", "tc"]


class FollowerSerializer(serializers.ModelSerializer):
    user_from = serializers.StringRelatedField(source="user_from.username")
    user_to = serializers.SlugRelatedField(
        slug_field="username", queryset=get_user_model().objects.all()
    )

    class Meta:
        model = Follower
        fields = "__all__"


class BlockSerializer(serializers.ModelSerializer):
    block_from = serializers.StringRelatedField(source="block_from.username")
    block_to = serializers.SlugRelatedField(
        slug_field="username", queryset=get_user_model().objects.all()
    )

    class Meta:
        model = Block
        fields = "__all__"

