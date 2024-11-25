# Generated by Django 3.0 on 2020-10-15 13:20

import django.core.validators
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("subjects", "0007_auto_20200921_1346"),
    ]

    operations = [
        migrations.AlterField(
            model_name="subject",
            name="nickname",
            field=models.CharField(
                default="-",
                help_text="Easy-to-remember name (e.g. 'Hercules').",
                max_length=64,
                validators=[
                    django.core.validators.RegexValidator(
                        "^[-._~\\+\\*\\w]+$", "Nicknames must only contain letters, numbers, or any of -._~."
                    )
                ],
            ),
        ),
    ]
