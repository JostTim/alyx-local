# Generated by Django 4.0.3 on 2022-06-21 19:10

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('jobs', '0006_alter_task_status'),
    ]

    operations = [
        migrations.RemoveConstraint(
            model_name='task',
            name='unique_task_name_per_session',
        ),
        migrations.AddField(
            model_name='task',
            name='arguments',
            field=models.JSONField(blank=True, help_text='dictionary of input arguments', null=True),
        ),
        migrations.AddConstraint(
            model_name='task',
            constraint=models.UniqueConstraint(fields=('name', 'session', 'arguments'), name='unique_name_arguments_per_session'),
        ),
    ]
