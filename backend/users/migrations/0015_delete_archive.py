# Generated by Django 5.1.3 on 2024-11-23 12:40

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0014_remove_block_unique_blocking_and_more'),
    ]

    operations = [
        migrations.DeleteModel(
            name='Archive',
        ),
    ]