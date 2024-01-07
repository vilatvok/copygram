from django.db import models
from django.contrib.auth.models import AbstractUser
from django.core.validators import MinLengthValidator
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.models import ContentType
from django.contrib.contenttypes.fields import GenericForeignKey
from django.db.models import UniqueConstraint

# Create your models here.


class User(AbstractUser):
    avatar = models.ImageField(upload_to="users/", blank=True)
    phone = models.CharField(
        unique=True,
        max_length=13,
        validators=([MinLengthValidator(12)]),
        null=True,
        blank=True,
    )
    online = models.BooleanField(default=False)


class Action(models.Model):
    owner = models.ForeignKey(
        get_user_model(), related_name="action", on_delete=models.CASCADE
    )
    date = models.DateTimeField(auto_now_add=True)
    act = models.CharField(max_length=255)
    image = models.ImageField()

    tc = models.ForeignKey(ContentType, on_delete=models.CASCADE, null=True, blank=True)
    ti = models.PositiveIntegerField(null=True, blank=True)
    target = GenericForeignKey("tc", "ti")

    class Meta:
        indexes = [models.Index(fields=["act"])]
        # constraints = [UniqueConstraint(fields=["owner", "act", "image"], name="act_unique")]
        ordering = ["-date"]

    def __str__(self):
        return f"{self.owner} {self.act}"


class Follower(models.Model):
    user_from = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="user_from"
    )
    user_to = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="user_to"
    )

    def __str__(self):
        return f"{self.user_from} followed {self.user_to}"


class Block(models.Model):
    block_from = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="block_from"
    )
    block_to = models.ForeignKey(
        get_user_model(), on_delete=models.CASCADE, related_name="block_to"
    )

    def __str__(self):
        return f"{self.block_from} blocked {self.block_to}"
