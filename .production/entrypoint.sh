#!/bin/sh

DUMP_DIR="/data"

echo "Django version installed"
echo python -m django --version

echo "Applying database migrations..."
python manage.py migrate --noinput 

# Find the latest .sql file in the DUMP_DIR directory
LATEST_DUMP_FILE=$(find "$DUMP_DIR" -maxdepth 1 -name '*.sql' -printf '%T+ %p\n' | sort -r | head -n1 | cut -d" " -f2)

# Check if a .sql dump file was found
if [ -n "$LATEST_DUMP_FILE" ]; then

    # Read the database password from the secret file
    DB_PASSWORD=$(cat /run/secrets/db-password)
    export PGPASSWORD="$DB_PASSWORD"

    echo -n "Creating missing database roles..."
    psql -h db -U postgres -d alyx -c "DO \$\$
    BEGIN
        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readaccess') THEN
            CREATE ROLE readaccess LOGIN;
            GRANT CONNECT ON DATABASE alyx TO readaccess;
            GRANT USAGE ON SCHEMA public TO readaccess;
            GRANT SELECT ON ALL TABLES IN SCHEMA public TO readaccess;
        END IF;

        IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'tjostmou') THEN
            CREATE ROLE tjostmou LOGIN;
            GRANT CONNECT ON DATABASE alyx TO tjostmou;
            GRANT USAGE ON SCHEMA public TO tjostmou;
            GRANT SELECT ON ALL TABLES IN SCHEMA public TO tjostmou;
        END IF;
    END
    \$\$;"

    # Run pg_restore on the db service 
    # (password is passed throug the ENV variable defined above, 
    # and host is the db service defined in compose.yaml)
    echo -n "Restoring database from $LATEST_DUMP_FILE..."
    pg_restore --clean -h db -U postgres -d alyx < "$LATEST_DUMP_FILE" && echo "OK"
else
    echo "No SQL dump file found in $DUMP_DIR. Skipping restore."
fi

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear --verbosity 0

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn 'alyx.wsgi' --bind=0.0.0.0:8000


