from django.contrib.auth import password_validation
from rest_framework import serializers

from common.serializers import CustomSerializer
from users import models
from users.utils import send_reset_email


class UserUpdateSerializer(
    CustomSerializer,
    serializers.HyperlinkedModelSerializer,
):
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
        model = models.User
        fields = [
            'url',
            'username',
            'email',
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


class UserSerializer(UserUpdateSerializer):
    def to_representation(self, instance):
        representation = super().to_representation(instance)
        current_user = self.context['request'].user
        user = instance
        privacy = user.privacy
        if privacy.online_status == 'followers':
            if not user.is_followed and current_user != user:
                representation.pop('is_online')
        elif privacy.online_status == 'nobody':
            representation.pop('is_online')
        return representation


class UserCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.User
        fields = [
            'username',
            'email',
            'avatar',
            'password',
        ]
        extra_kwargs = {'password': {'write_only': True}}

    def validate_password(self, value):
        password_validation.validate_password(value)
        return value

    def create(self, validated_data):
        request = self.context['request']
        ref = request.query_params.get('ref')
        user = models.User.objects.create_user(**validated_data)
        link = 'https://copygram.com/api/register-confirm'
        send_reset_email(user, link, ref)
        return user


class UserPrivacySerializer(serializers.ModelSerializer):
    class Meta:
        model = models.UserPrivacy
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
        model = models.Action
        exclude = ['content_type', 'object_id']


class ReportSerializer(serializers.ModelSerializer):
    class Meta:
        model = models.Report
        fields = ['reason']


class ReferralSerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField(source='referred_by')

    class Meta:
        model = models.Referral
        fields = ['id', 'user', 'created_at']

    def to_representation(self, instance):
        representation = super().to_representation(instance)
        user = representation['user']
        if user is None:
            representation['user'] = 'User has been deleted'
        return representation


class VipSerializer(serializers.Serializer):
    duration = serializers.IntegerField(min_value=0)


class UserActivitySerializer(serializers.Serializer):
    login_time = serializers.DateTimeField(format='%H:%M:%S')
    logout_time = serializers.DateTimeField(format='%H:%M:%S')
    session_time = serializers.DurationField()

    class Meta:
        model = models.UserActivity
        fields = ['login_time', 'logout_time', 'session_time']


class UserDayActivitySerializer(serializers.ModelSerializer):
    user = serializers.StringRelatedField()
    day_activities = UserActivitySerializer(
        many=True,
        read_only=True,
        source='get_day_activities',
    )

    class Meta:
        model = models.UserDayActivity
        fields = ['user', 'date', 'total_activity', 'day_activities']
