from django.contrib.auth import get_user_model, password_validation

from rest_framework import serializers

from common.utils import CustomSerializer

from blogs.models import Post
from users.models import Action, Report, UserPrivacy


User = get_user_model()


class UserSerializer(CustomSerializer, serializers.HyperlinkedModelSerializer):
    url = serializers.HyperlinkedIdentityField(
        view_name='user-detail',
        lookup_field='slug',
    )
    followers = serializers.IntegerField(
        read_only=True,
        source='followers_count',
    )
    following = serializers.IntegerField(
        read_only=True,
        source='following_count',
    )

    class Meta:
        model = User
        fields = [
            'url',
            'username',
            'last_login',
            'bio',
            'gender',
            'avatar',
            'is_online',
            'followers',
            'following',
        ]
        extra_kwargs = {
            'last_login': {'read_only': True},
            'is_online': {'read_only': True},
        }


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


class UserPrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserPrivacy
        exclude = ['user']


class PasswordSerializer(serializers.Serializer):
    password = serializers.CharField(write_only=True)

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value


class PasswordResetSerializer(serializers.Serializer):
    email = serializers.EmailField(write_only=True)


class PasswordResetConfirmSerializer(serializers.Serializer):
    new_password = serializers.CharField(write_only=True)

    def validate(self, data):
        password_validation.validate_password(data['new_password'])
        return data


class ActionSerializer(serializers.ModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    target = serializers.StringRelatedField()

    class Meta:
        model = Action
        exclude = ['content_type', 'object_id']


class ActivitySerializer(serializers.HyperlinkedModelSerializer):
    owner = serializers.ReadOnlyField(source='owner.username')
    file = serializers.CharField()

    class Meta:
        model = Post
        fields = ['url', 'owner', 'file']


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = Report
        fields = ['reason']