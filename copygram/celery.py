import os

from celery import Celery
from django.conf import settings

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'copygram.settings')

app = Celery('copygram')
app.config_from_object('django.conf:settings')
app.conf.broker_url = settings.CELERY_BROKER
app.autodiscover_tasks()

