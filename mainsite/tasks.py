import json

from datetime import timedelta

from celery import shared_task
from django_celery_beat.models import PeriodicTask, CrontabSchedule

from mainsite.models import Story


@shared_task
def delete_story(story_id):
    """
    Remove story after 24 hours.
    """
    story = Story.objects.get(id=story_id)
    story.delete()


def delete_story_scheduler(story_id, story_date):
    date = story_date + timedelta(days=1)
    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute=date.minute,
        hour=date.hour,
        day_of_month=date.day,
        month_of_year=date.month,
    )
    PeriodicTask.objects.create(
        crontab=crontab,
        name=f'delete-story-{story_id}',
        task='users.tasks.delete_story',
        args=json.dumps([story_id]),
        one_off=True
    )