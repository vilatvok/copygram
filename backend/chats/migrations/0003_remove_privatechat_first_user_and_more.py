# Generated by Django 5.1.3 on 2024-11-29 12:52

import django.db.models.deletion
from django.conf import settings
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('chats', '0002_alter_message_options_alter_roomchat_options_and_more'),
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
    ]

    operations = [
        migrations.RemoveField(
            model_name='privatechat',
            name='first_user',
        ),
        migrations.RemoveField(
            model_name='privatechat',
            name='second_user',
        ),
        migrations.AddField(
            model_name='privatechat',
            name='users',
            field=models.ManyToManyField(related_name='private_chats', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='message',
            name='content_type',
            field=models.ForeignKey(limit_choices_to={'model__in': ('groupchat', 'privatechat')}, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.CreateModel(
            name='GroupChat',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('created_at', models.DateTimeField(auto_now_add=True)),
                ('image', models.ImageField(default='static/images/group.png', upload_to='rooms/%Y/%m/%d/')),
                ('name', models.CharField(max_length=50)),
                ('owner', models.ForeignKey(default=None, on_delete=django.db.models.deletion.SET_DEFAULT, related_name='group_owner', to=settings.AUTH_USER_MODEL)),
                ('users', models.ManyToManyField(related_name='group_chats', to=settings.AUTH_USER_MODEL)),
            ],
            options={
                'ordering': ['-created_at'],
                'abstract': False,
            },
        ),
        migrations.DeleteModel(
            name='RoomChat',
        ),
    ]
