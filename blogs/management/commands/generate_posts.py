from django.core.files.base import ContentFile
from django.core.management.base import BaseCommand, CommandParser

from faker import Faker

from users.models import User
from blogs.models import Post, PostMedia


class Command(BaseCommand):
    def add_arguments(self, parser: CommandParser) -> None:
        parser.add_argument('--count', dest='count', type=int)

    def handle(self, *args, **options):
        fake = Faker()
        count = options['count']
        for _ in range(count):
            user = User.objects.order_by('?')[0]
            file_extension = fake.file_name(extension='jpeg')
            file = ContentFile(fake.image(), name=file_extension)
            p = Post.objects.create(owner=user)
            PostMedia.objects.create(post=p, file=file)
