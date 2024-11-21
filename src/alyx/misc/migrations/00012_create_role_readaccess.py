from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("misc", "00011_create_natsort_collation"),
    ]

    operations = [
        migrations.RunSQL(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readaccess') THEN
                    CREATE ROLE readaccess LOGIN;
                    GRANT CONNECT ON DATABASE alyx TO readaccess;
                    GRANT USAGE ON SCHEMA public TO readaccess;
                    GRANT SELECT ON ALL TABLES IN SCHEMA public TO readaccess;
                END IF;
            END
            $$;
            """
        ),
    ]
