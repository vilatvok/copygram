from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import (
    GenericForeignKey,
    GenericRelation,
)
from django.utils.text import slugify

from users.managers import CustomUserManager


class User(AbstractUser):
    """Override default user model."""
    GENDER = [
        ('male', 'Male'),
        ('female', 'Female')
    ]

    slug = models.SlugField(unique=True, max_length=255)
    avatar = models.ImageField(
        upload_to='users/%Y/%m/%d/',
        blank=True,
        null=True,
    )
    email = models.EmailField()
    is_online = models.BooleanField(default='False')
    last_activity = models.DateTimeField(blank=True, null=True)
    user_actions = GenericRelation(to='Action', related_query_name='user')
    bio = models.TextField(blank=True)
    gender = models.CharField(choices=GENDER)

    objects = CustomUserManager()

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__username = self.username

    def save(self, *args, **kwargs):
        if not self.slug or self.__username != self.username:
            self.slug = slugify(self.username)
        return super().save(*args, **kwargs)
    

class UserPrivacy(models.Model):
    COMMENTS = [
        ('everyone', 'Everyone'),
        ('followers', 'Followers'),
    ]
    LIKES = [
        ('everyone', 'Everyone'),
        ('followers', 'Followers'),
        ('nobody', 'Nobody'),
    ]

    user = models.OneToOneField(
        to='User',
        primary_key=True,
        on_delete=models.CASCADE,
        related_name='privacy',
    )
    private_account = models.BooleanField(default=False)
    likes = models.CharField(
        choices=LIKES,
        max_length=15,
        default='everyone',
    )
    comments = models.CharField(
        choices=COMMENTS,
        max_length=15,
        default='everyone',
    )
    online_status = models.CharField(
        choices=LIKES,
        max_length=15,
        default='everyone',
    )
    
    class Meta:
        verbose_name_plural = 'Users privacy'


class Action(models.Model):
    """
    Model for all posible actions in project.
    Contains a generic foreign key to pair with each model.
    """
    owner = models.ForeignKey(
        to='User',
        related_name='actions',
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField(auto_now_add=True)
    act = models.CharField(max_length=255)
    file = models.FileField()
    unread = models.BooleanField(default=True)
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ('post', 'comment', 'user')}
    )
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')

    def __str__(self):
        return f'{self.owner} {self.act}'


class Follower(models.Model):
    from_user = models.ForeignKey(
        to='User',
        on_delete=models.CASCADE,
        related_name='following',
    )
    to_user = models.ForeignKey(
        to='User',
        on_delete=models.CASCADE,
        related_name='followers',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['from_user', 'to_user'],
                name='unique_followers',
            ),
        ]

    def __str__(self):
        return f'{self.from_user} followed {self.to_user}'


class Block(models.Model):
    block_from = models.ForeignKey(
        to='User',
        on_delete=models.CASCADE,
        related_name='blocked',
    )
    block_to = models.ForeignKey(
        to='User',
        on_delete=models.CASCADE,
        related_name='blocked_by',
    )

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['block_from', 'block_to'],
                name='unique_blocking',
            ),
        ]

    def __str__(self):
        return f'{self.block_from} blocked {self.block_to}'


class Report(models.Model):
    report_from = models.ForeignKey(
        to='User',
        on_delete=models.SET_NULL,
        null=True,
        related_name='reports',
    )
    report_on = models.ForeignKey(
        to='User',
        on_delete=models.CASCADE,
        related_name='reports_by',
    )
    reason = models.TextField()
    date = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f'{self.report_from} report on {self.report_on}'


class Archive(models.Model):
    content_type = models.ForeignKey(
        to=ContentType,
        on_delete=models.CASCADE,
        limit_choices_to={'model__in': ('post', 'story')},
    )
    object_id = models.PositiveIntegerField()
    target = GenericForeignKey('content_type', 'object_id')

    class Meta:
        constraints = [
            models.UniqueConstraint(
                fields=['content_type', 'object_id'],
                name='unique_archive',
            ),
        ]
