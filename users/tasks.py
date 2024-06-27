import json

from datetime import timedelta, datetime

from celery import shared_task

from django_celery_beat.models import PeriodicTask, CrontabSchedule

from common.utils import redis_client
from users.models import User


@shared_task
def cancel_vip(user_id):
    redis_client.srem('active_vip_users', user_id)


@shared_task
def delete_account(user_id):
    user = User.objects.get(id=user_id)
    user.delete()


def delete_account_scheduler(user_id):
    date = datetime.now() + timedelta(hours=6)
    crontab, _ = CrontabSchedule.objects.get_or_create(
        minute=date.minute,
        hour=date.hour,
        day_of_month=date.day,
        month_of_year=date.month,
    )
    PeriodicTask.objects.create(
        crontab=crontab,
        name=f'delete-user-{user_id}',
        task='users.tasks.delete_account',
        args=json.dumps([user_id]),
        one_off=True,
    )

