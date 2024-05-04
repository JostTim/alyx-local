# Generated by Django 2.1 on 2018-11-19 09:30
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
from django.utils import timezone
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("misc", "0001_initial"),
    ]

    operations = [
        migrations.CreateModel(
            name="CageType",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(blank=True, help_text="Long name", max_length=255)),
                (
                    "json",
                    django.contrib.postgres.fields.jsonb.JSONField(
                        blank=True, help_text="Structured data, formatted in a user-defined way", null=True
                    ),
                ),
                (
                    "description",
                    models.CharField(
                        blank=True, help_text="Extended description of the cage product/brand", max_length=1023
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.AddField(
            model_name="lab",
            name="reference_weight_pct",
            field=models.FloatField(
                default=0.0,
                help_text="The minimum mouse weight is a linear combination of the reference weight and the zscore weight.",
            ),
        ),
        migrations.AddField(
            model_name="lab",
            name="zscore_weight_pct",
            field=models.FloatField(
                default=0.0,
                help_text="The minimum mouse weight is a linear combination of the reference weight and the zscore weight.",
            ),
        ),
        migrations.AddField(
            model_name="lab",
            name="cage_type",
            field=models.ForeignKey(
                blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, to="misc.CageType"
            ),
        ),
        migrations.AlterField(
            model_name="labmembership",
            name="start_date",
            field=models.DateField(blank=True, null=True, default=timezone.now),
        ),
    ]
