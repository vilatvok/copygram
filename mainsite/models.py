from django.utils import timezone

from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation

from taggit.managers import TaggableManager

from users.models import Action


User = get_user_model()


class Base(models.Model):
    """Abstract model. Is used for other models."""
    owner = models.ForeignKey(
        User, related_name='%(class)s_owner', on_delete=models.CASCADE
    )
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-date']


class Post(Base):
    description = models.TextField(blank=True)
    tags = TaggableManager(blank=True)
    is_like = models.ManyToManyField(User, related_name='like', blank=True)
    is_comment = models.BooleanField(default=True)
    post_action = GenericRelation(Action, related_query_name='post')
    
    def __str__(self):
        return f'{self.owner}'
    
    def save(self, *args, **kwargs):
        if not self.pk:
            self.owner.last_activity = timezone.now()
            self.owner.save()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('mainsite:post', kwargs={'post_id': self.pk})


class PostMedia(models.Model):
    post = models.ForeignKey('Post', related_name='files', on_delete=models.CASCADE)
    file = models.FileField(upload_to='posts/')


class Comment(Base):
    post = models.ForeignKey('Post', on_delete=models.CASCADE, related_name='comments')
    text = models.CharField(max_length=255)

    def __str__(self):
        return f'{self.owner} commented {self.post}'


class Story(Base):
    img = models.ImageField(upload_to='stories/')

    class Meta:
        verbose_name_plural = 'Stories'    

    def __str__(self):
        return f'{self.owner} public story'
