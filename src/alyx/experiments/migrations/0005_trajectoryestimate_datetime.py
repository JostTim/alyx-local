# Generated by Django 2.2.6 on 2020-06-08 12:40

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("experiments", "0004_auto_20200519_2129"),
    ]

    operations = [
        migrations.AddField(
            model_name="trajectoryestimate",
            name="datetime",
            field=models.DateTimeField(auto_now=True, verbose_name="last update"),
        ),
    ]
