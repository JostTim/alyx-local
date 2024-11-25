# Generated by Django 4.1.3 on 2023-06-14 19:10

import django.core.validators
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0016_dataset_filerecord_retrocompatible"),
    ]

    operations = [
        migrations.AlterField(
            model_name="dataformat",
            name="file_extension",
            field=models.CharField(
                help_text="file extension, starting with a dot.",
                max_length=255,
                unique=True,
                validators=[
                    django.core.validators.RegexValidator(
                        "^\\.[^\\.]+$",
                        code="invalid_file_extension",
                        message="Invalid file extension, should start with a dot",
                    )
                ],
            ),
        ),
        migrations.AlterField(
            model_name="dataset",
            name="data_repository",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="data.datarepository"
            ),
        ),
    ]
