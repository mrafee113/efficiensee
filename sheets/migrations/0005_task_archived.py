# Generated by Django 4.0 on 2022-08-19 08:57

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('sheets', '0004_alter_entry_date_alter_entry_duration_and_more'),
    ]

    operations = [
        migrations.AddField(
            model_name='task',
            name='archived',
            field=models.BooleanField(default=False),
        ),
    ]