from celery import shared_task

from django.utils import timezone

from datetime import timedelta


@shared_task
def check_story():
    from mainsite.models import Story

    recent = timezone.now() - timedelta(hours=24)
    story = Story.objects.filter(date__lte=recent)
    story.delete()
