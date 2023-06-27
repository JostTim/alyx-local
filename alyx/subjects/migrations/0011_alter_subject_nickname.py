# Generated by Django 4.1.7 on 2023-05-11 16:24

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('subjects', '0010_auto_20210624_1253'),
    ]

    operations = [
        migrations.AlterField(
            model_name='subject',
            name='nickname',
            field=models.CharField(default='-', help_text="Easy-to-remember name (e.g. 'Hercules').", max_length=64, validators=[django.core.validators.RegexValidator('^[\\w-]+$', 'Nicknames must only contain letters, numbers, hyphens and underscores.')]),
        ),
    ]
