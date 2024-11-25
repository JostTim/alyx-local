# Generated by Django 2.2.6 on 2020-08-20 16:23

from django.db import migrations, models


def update_qc_not_set_value(apps, schema_editor):
    Session = apps.get_model("actions", "Session")
    Session.objects.filter(qc=20).update(qc=0)


class Migration(migrations.Migration):

    dependencies = [
        ("actions", "0011_auto_20200317_1055"),
    ]

    operations = [
        migrations.AlterField(
            model_name="session",
            name="qc",
            field=models.IntegerField(
                choices=[(50, "CRITICAL"), (40, "FAIL"), (30, "WARNING"), (0, "NOT_SET"), (10, "PASS")], default=0
            ),
        ),
        migrations.RunPython(update_qc_not_set_value),
    ]
