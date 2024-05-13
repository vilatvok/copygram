import os

from django.conf import settings

from celery import Celery


os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'copygram.settings')

app = Celery('copygram')
app.config_from_object('django.conf:settings')
app.conf.broker_url = settings.CELERY_BROKER
app.conf.beat_scheduler = settings.CELERY_BEAT_SCHEDULER
app.autodiscover_tasks()
