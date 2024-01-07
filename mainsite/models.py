from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.conf import settings
from taggit.managers import TaggableManager

from .tasks import count_p


# Create your models here.
class Base(models.Model):
    owner = models.ForeignKey(
        get_user_model(), related_name="%(class)s_owner", on_delete=models.CASCADE
    )
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-date']


class Post(Base):
    photo = models.ImageField(upload_to="post/")
    description = models.TextField(blank=True, null=True)
    tags = TaggableManager(blank=True)
    is_like = models.ManyToManyField(get_user_model(), related_name="like", blank=True)
    total_likes = models.PositiveIntegerField(default=0)
    is_comment = models.BooleanField(default=True)

    class Meta:
        indexes = [
            models.Index(fields=['description'])
        ]
    
    def __str__(self):
        return f"{self.owner}"

    def get_absolute_url(self):
        return reverse("mainsite:post", kwargs={"post_id": self.pk})

    def save(self, *args, **kwargs):
        count_p.delay(self.id)
        return super().save(*args, **kwargs)


class Comment(Base):
    post = models.ForeignKey("Post", on_delete=models.CASCADE, related_name="comments")
    text = models.CharField(max_length=255)

    def __str__(self):
        return f"{self.owner} commented {self.post}"


class Story(Base):
    img = models.ImageField(upload_to="story/")

    class Meta:
        verbose_name_plural = "Stories"    

    def __str__(self):
        return f"{self.owner} public story"


# user = get_user_model()
# user.add_to_class('following', models.ManyToManyField('self',
#                                                         through=Follower,
#                                                         related_name='follows',
#                                                         symmetrical=False))
