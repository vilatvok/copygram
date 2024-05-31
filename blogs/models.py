from django.utils import timezone
from django.db import models
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.contrib.contenttypes.fields import GenericRelation

from tree_queries.models import TreeNode

from taggit.managers import TaggableManager

from blogs.managers import CommentQuerySet, PostManager
from users.models import Action, Archive


User = get_user_model()


class Base(models.Model):
    """Abstract model. Is used for other models."""
    owner = models.ForeignKey(
        to=User,
        related_name='%(class)ss',
        on_delete=models.CASCADE,
    )
    date = models.DateTimeField(auto_now_add=True)

    class Meta:
        abstract = True
        ordering = ['-date']


class Post(Base):
    description = models.TextField(blank=True)
    likes = models.ManyToManyField(User, related_name='likes', blank=True)
    saved = models.ManyToManyField(User, related_name='saved', blank=True)
    is_comment = models.BooleanField(default=True)
    actions = GenericRelation(Action, related_query_name='post')
    archived = models.BooleanField(default=False)
    archived_posts = GenericRelation(Archive, related_query_name='post')
    tags = TaggableManager(blank=True)

    objects = PostManager()

    def save(self, *args, **kwargs):
        if not self.pk:
            self.owner.last_activity = timezone.now()
            self.owner.save()
        return super().save(*args, **kwargs)

    def get_absolute_url(self):
        return reverse('blogs:post', kwargs={'post_id': self.pk})

    def get_files(self):
        return self.files.select_related('post')

    def get_tags(self):
        return self.tags.all()


class PostMedia(models.Model):
    post = models.ForeignKey(
        to=Post,
        related_name='files',
        on_delete=models.CASCADE,
    )
    file = models.FileField(upload_to='posts/%Y/%m/%d/')

    class Meta:
        verbose_name_plural = 'Posts media'


class Comment(TreeNode):
    owner = models.ForeignKey(
        to=User,
        related_name='comments',
        on_delete=models.CASCADE,
    )
    post = models.ForeignKey(
        to='Post',
        on_delete=models.CASCADE,
        related_name='comments',
    )
    parent = models.ForeignKey(
        to='self',
        on_delete=models.CASCADE,
        blank=True,
        null=True,
        related_name='replies',
    )
    likes = models.ManyToManyField(
        to=User,
        related_name='comment_likes',
        blank=True,
    )
    text = models.CharField(max_length=255)
    date = models.DateTimeField(auto_now_add=True)

    objects = CommentQuerySet.as_manager()

    class Meta:
        ordering = ['-date']

    def __str__(self):
        if self.parent:
            return f'Comment to ({self.post.id})->{self.parent.id}->{self.id}'
        else:
            return f'Comment to ({self.post.id})->{self.id}' 


class Story(Base):
    img = models.ImageField(upload_to='stories/%Y/%m/%d/')
    archived = models.BooleanField(default=False)
    archived_stories = GenericRelation(Archive, related_query_name='story')

    class Meta:
        verbose_name_plural = 'Stories'
