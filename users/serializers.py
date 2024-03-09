from django.contrib.auth import get_user_model, password_validation

from rest_framework import serializers
from rest_framework.fields import empty

from common.utils import set_serializer_fields

from mainsite.models import Post
from users.models import Action


User = get_user_model()


class UserSerializer(serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='user-detail', lookup_field='slug'
    )
    followers_count = serializers.IntegerField(read_only=True)
    following_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = User
        fields = [
            'url',
            'username',
            'last_login',
            'bio',
            'gender',
            'avatar',
            'private_account',
            'followers_count',
            'following_count',
        ]
        extra_kwargs = {
            'private_account': {'write_only': True},
            'last_login': {'read_only': True}
        }

    def __init__(self, instance=None, data=empty, **kwargs):
        fields = kwargs.pop('fields', None)
        super().__init__(instance, data, **kwargs)
        if fields:
            set_serializer_fields(fields, self.fields)


class UserCreateSerializer(UserSerializer):
    class Meta:
        model = User
        fields = UserSerializer.Meta.fields + ['password']
        extra_kwargs = {
            **UserSerializer.Meta.extra_kwargs,
            'password': {'write_only': True}
        }

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value
    
    def create(self, validated_data):
        return User.objects.create_user(**validated_data)
        

class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value
    

class ActionSerializer(serializers.ModelSerializer):
    owner = serializers.StringRelatedField(source='owner.username')
    target = serializers.StringRelatedField()

    class Meta:
        model = Action
        exclude = ['content_type', 'object_id']


class ActivitySerializer(serializers.ModelSerializer):
    file = serializers.CharField()

    class Meta:
        model = Post
        fields = ['id', 'owner', 'file']