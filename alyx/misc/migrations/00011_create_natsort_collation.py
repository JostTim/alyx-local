from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("misc", "00010_create_admin_user"),
    ]

    operations = [
        migrations.RunSQL(
            """
            CREATE COLLATION IF NOT EXISTS natsort_collation (provider = icu, LOCALE = 'en@colNumeric=yes');
            ALTER COLLATION natsort_collation OWNER TO postgres;
            """
        ),
        migrations.RunSQL(
            """
            ALTER TABLE subjects_subject ALTER COLUMN nickname TYPE character varying(64) COLLATE natsort_collation;
            """
        ),
    ]
