# Generated by Django 5.1.3 on 2024-11-23 12:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0003_uninterestingpost_unique_uninteresting_post'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='post',
            options={'ordering': ['-date']},
        ),
    ]
