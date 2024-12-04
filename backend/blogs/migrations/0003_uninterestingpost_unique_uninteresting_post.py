# Generated by Django 5.1.3 on 2024-11-11 12:47

from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0002_uninterestingpost'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.AddConstraint(
            model_name='uninterestingpost',
            constraint=models.UniqueConstraint(fields=('user', 'post'), name='unique_uninteresting_post'),
        ),
    ]
