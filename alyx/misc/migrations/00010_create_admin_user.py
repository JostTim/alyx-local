from django.db import migrations, models
from django.contrib.auth import get_user_model


def create_admin_user(apps, schema_editor):
    LabMember = get_user_model()
    if not LabMember.objects.filter(username="admin").exists():
        LabMember.objects.create_superuser("admin", email="admin@example.com", password="admin")


class Migration(migrations.Migration):

    dependencies = [
        ("misc", "0009_auto_20211122_1535"),
    ]

    operations = [
        migrations.RunPython(create_admin_user, reverse_code=migrations.RunPython.noop),
    ]
