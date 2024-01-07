from celery import shared_task
from celery_singleton import Singleton

from django.core.mail import send_mail


@shared_task
def send_notification():
    return send_mail(
        "Lotery", "You won nokia 3310", "kvydyk@gmail.com", ["kovtalivt@gmail.com"]
    )


@shared_task(base=Singleton)
def count_p(post_id):
    from mainsite.models import Post

    post = Post.objects.get(id=post_id)
    if post.total_likes != post.is_like.count():
        post.total_likes = post.is_like.count()

        post.save()

