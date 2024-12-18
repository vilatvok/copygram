# Generated by Django 5.1.3 on 2024-11-26 10:42

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0015_delete_archive'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='action',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='referral',
            options={'ordering': ['-created_at']},
        ),
        migrations.AlterModelOptions(
            name='report',
            options={'ordering': ['-created_at']},
        ),
        migrations.RenameField(
            model_name='action',
            old_name='date',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='referral',
            old_name='date_joined',
            new_name='created_at',
        ),
        migrations.RenameField(
            model_name='report',
            old_name='date',
            new_name='created_at',
        ),
    ]
