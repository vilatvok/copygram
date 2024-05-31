import json

from datetime import timedelta

from celery import shared_task

from django.db import transaction
from django.contrib.contenttypes.models import ContentType
from django_celery_beat.models import PeriodicTask, CrontabSchedule

from blogs.models import Story
from users.models import Archive


@shared_task
def archive_story(story_id):
    """
    Remove story after 24 hours.
    """
    story = Story.objects.get(id=story_id)
    target_ct = ContentType.objects.get_for_model(story)
    story.archived = True
    with transaction.atomic():
        story.save()
        Archive.objects.create(content_type=target_ct, object_id=story.id)


def archive_story_scheduler(story_id, story_date):
    date = story_date + timedelta(days=1)
    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute=date.minute,
        hour=date.hour,
        day_of_month=date.day,
        month_of_year=date.month,
    )
    PeriodicTask.objects.create(
        crontab=crontab,
        name=f'archive-story-{story_id}',
        task='blogs.tasks.archive_story',
        args=json.dumps([story_id]),
        one_off=True,
    )
