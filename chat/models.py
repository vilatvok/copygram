from django.db import models
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericForeignKey, GenericRelation
from django.contrib.contenttypes.models import ContentType


User = get_user_model()


class RoomChat(models.Model):
    owner = models.ForeignKey(
        User, on_delete=models.SET_DEFAULT, default=None, related_name='room_owner'
    )
    image = models.ImageField(upload_to='rooms/', default='static/images/group.png')
    name = models.CharField(max_length=50)
    created = models.DateTimeField(auto_now_add=True)
    users = models.ManyToManyField(User, related_name='rooms')
    messages = GenericRelation(
        'Message', 
        related_query_name='room_chat'
    )

    def __str__(self):
        return self.name


class PrivateChat(models.Model):
    first_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='first_private'
    )
    second_user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='second_private'
    )
    messages = GenericRelation(
        'Message', 
        related_query_name='private_chat'
    )


class Message(models.Model):
    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name='messages'
    )
    content = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.PositiveIntegerField()
    chat = GenericForeignKey('content_type', 'object_id')


class MessageImages(models.Model):
    message = models.ForeignKey(
        Message, 
        on_delete=models.CASCADE, 
        related_name='files'
    )
    file = models.FileField(blank=True, upload_to='messages/')
