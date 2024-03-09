from django.db import models
from django.contrib.auth.models import AbstractUser
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.utils.text import slugify


class User(AbstractUser):
    """Override default user model."""
    GENDER = [
        ('male', 'Male'),
        ('female', 'Female')
    ]

    slug = models.SlugField(unique=True, max_length=255)
    avatar = models.ImageField(upload_to='users/', blank=True, null=True)
    email = models.EmailField()
    last_activity = models.DateTimeField(blank=True, null=True)
    user_action = GenericRelation('Action', related_query_name='user')
    bio = models.TextField(blank=True)
    gender = models.CharField(choices=GENDER)
    private_account = models.BooleanField(default=False)

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.__username = self.username

    def save(self, *args, **kwargs):
        if not self.slug or self.__username != self.username:
            self.slug = slugify(self.username)
        return super().save(*args, **kwargs)


class Action(models.Model):
    """
    Model for all posible actions in project.
    Contains a generic foreign key to pair with each model.
    """
    owner = models.ForeignKey(
        'User', related_name='action', on_delete=models.CASCADE
    )
    date = models.DateTimeField(auto_now_add=True)
    act = models.CharField(max_length=255)
    file = models.FileField()
    unread = models.BooleanField(default=True) 
    content_type = models.ForeignKey(
        ContentType, 
        on_delete=models.CASCADE, 
        null=True, 
        blank=True
    )
    object_id = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey('content_type', 'object_id')

    class Meta:
        indexes = [models.Index(fields=['act'])]
        ordering = ['-date']

    def __str__(self):
        return f'{self.owner} {self.act}'


class Follower(models.Model):
    user_from = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='user_from'
    )
    user_to = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='user_to'
    )

    def __str__(self):
        return f'{self.user_from} followed {self.user_to}'


class Block(models.Model):
    block_from = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='block_from'
    )
    block_to = models.ForeignKey(
        'User', on_delete=models.CASCADE, related_name='block_to'
    )

    def __str__(self):
        return f'{self.block_from} blocked {self.block_to}'
