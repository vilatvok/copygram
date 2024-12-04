# Generated by Django 5.1.3 on 2024-11-11 10:19

import django.db.models.expressions
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('users', '0010_useractivity'),
    ]

    operations = [
        migrations.AddField(
            model_name='useractivity',
            name='session_time',
            field=models.GeneratedField(db_persist=True, expression=django.db.models.expressions.CombinedExpression(models.F('logout_time'), '-', models.F('login_time')), output_field=models.DurationField()),
        ),
    ]
