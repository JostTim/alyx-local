# Generated by Django 2.2.6 on 2020-03-09 15:13

import django.contrib.postgres.fields.jsonb
from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("actions", "0009_ephyssession"),
    ]

    operations = [
        migrations.AddField(
            model_name="session",
            name="extended_qc",
            field=django.contrib.postgres.fields.jsonb.JSONField(
                blank=True, help_text="Structured data about session QC,formatted in a user-defined way", null=True
            ),
        ),
    ]
