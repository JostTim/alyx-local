# Generated by Django 2.1 on 2019-04-09 11:02

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data", "0003_auto_20190315_1716"),
        ("misc", "0004_auto_20190309_1750"),
    ]

    operations = [
        migrations.AddField(
            model_name="lab",
            name="repositories",
            field=models.ManyToManyField(
                blank=True,
                help_text="Related DataRepository instances. "
                "Any file which is registered to Alyx is automatically copied "
                "to all repositories assigned to its project.",
                to="data.DataRepository",
            ),
        ),
    ]
