from django.db import transaction

from common.utils import create_action



def like_post(user, post):
    first_image = post.files.first()
    if post.likes.filter(id=user.id).exists():
        post.likes.remove(user)
        status = 'Unliked'
    # if post has been already liked, then unlike post.
    else:
        with transaction.atomic():
            post.likes.add(user)
            if user != post.owner:
                create_action(user, 'liked post', post, first_image.file)
        status = 'Liked'
    post.save()
    return status


def save_post(user, post):
    if post.saved.filter(id=user.id).exists():
        post.saved.remove(user)
        status = 'Removed'
    else:
        post.saved.add(user)
        status = 'Saved'
    post.save()
    return status
