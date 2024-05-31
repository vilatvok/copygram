from datetime import timedelta

from django.utils import timezone
from django.conf import settings
from django.db.models import Count
from django.core.mail import send_mass_mail
from django.core.management.base import BaseCommand, CommandParser
from django.contrib.auth import get_user_model


class Command(BaseCommand):
    help = 'Send a message to user'

    def add_arguments(self, parser: CommandParser):
        parser.add_argument('--days', dest='days', type=int)

    def handle(self, *args, **options):
        emails = []
        days = options['days']
        date = timezone.now() - timedelta(days=days or 3)
        users = (
            get_user_model().objects.annotate(count_post=Count('posts')).
            filter(count_post=0, last_activity__lte=date)
        )
        for user in users:
            time_ago = (timezone.now() - user.last_activity).days
            msg = f"""Last time you published your post {time_ago} days ago.
            Let's go to publish your first post."""
            emails.append((
                'Publish your first post',
                msg,
                settings.EMAIL_HOST_USER,
                [user.email]
            ))
        send_mass_mail(emails)
