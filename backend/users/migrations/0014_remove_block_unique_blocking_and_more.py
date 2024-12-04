# Generated by Django 5.1.3 on 2024-11-23 07:38

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0013_remove_action_unread'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='block',
            name='unique_blocking',
        ),
        migrations.RenameField(
            model_name='block',
            old_name='block_from',
            new_name='from_user',
        ),
        migrations.RenameField(
            model_name='block',
            old_name='block_to',
            new_name='to_user',
        ),
        migrations.AddConstraint(
            model_name='block',
            constraint=models.UniqueConstraint(fields=('from_user', 'to_user'), name='unique_blocking'),
        ),
        migrations.AddConstraint(
            model_name='block',
            constraint=models.CheckConstraint(condition=models.Q(('from_user', models.F('to_user')), _negated=True), name='self_blocking'),
        ),
    ]
