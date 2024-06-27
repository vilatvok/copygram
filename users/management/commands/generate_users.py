from django.core.management.base import BaseCommand, CommandParser

from faker import Faker

from users.models import User


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--count', dest='count', type=int)

    def handle(self, *args, **options) -> str | None:
        fake = Faker()
        count = options['count']
        for _ in range(count):
            User.objects.create(
                username=fake.user_name(),
                email=fake.email(),
                password=fake.password()
            )
