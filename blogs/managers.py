from django.db import models

from tree_queries.query import TreeQuerySet


class PostManager(models.Manager):
    def annotated(self):
        from blogs.models import PostMedia
        subquery = PostMedia.objects.filter(post=models.OuterRef('pk'))
        objs = self.annotate(
            likes_count=models.Count('likes'),
            file=models.Subquery(subquery.values('file')[:1]),
        ).select_related('owner')
        return objs


class CommentQuerySet(TreeQuerySet):
    def with_likes(self):
        return self.annotate(likes_count=models.Count('likes'))
