# Generated by Django 4.2.13 on 2024-11-05 08:57

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('blogs', '0001_initial'),
        ('users', '0003_follower_self_following'),
    ]

    operations = [
        migrations.AlterField(
            model_name='user',
            name='gender',
            field=models.CharField(choices=[('male', 'Male'), ('female', 'Female')], default='male', max_length=6),
        ),
        migrations.AlterField(
            model_name='userprivacy',
            name='comments',
            field=models.CharField(choices=[('everyone', 'Everyone'), ('followers', 'Followers'), ('nobody', 'Nobody')], default='everyone', max_length=10),
        ),
        migrations.AlterField(
            model_name='userprivacy',
            name='likes',
            field=models.CharField(choices=[('everyone', 'Everyone'), ('followers', 'Followers'), ('nobody', 'Nobody')], default='everyone', max_length=10),
        ),
        migrations.AlterField(
            model_name='userprivacy',
            name='online_status',
            field=models.CharField(choices=[('everyone', 'Everyone'), ('followers', 'Followers'), ('nobody', 'Nobody')], default='everyone', max_length=10),
        ),
        migrations.CreateModel(
            name='ContentPreferences',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('preference', models.CharField(choices=[('interested', 'Interested'), ('not_interested', 'Not interested')], default='interested', max_length=15)),
                ('post', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to='blogs.post')),
                ('user', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='preferences', to=settings.AUTH_USER_MODEL)),
            ],
        ),
    ]