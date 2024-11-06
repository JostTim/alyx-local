#!/bin/bash

DUMP_DIR="/data"

# source .venv/bin/activate

echo -n "Django version:" && echo -n $(pdm run python -m django --version) && echo " is installed"

echo "Applying database migrations..."
pdm run manage.py migrate --noinput 

# Find the latest .sql file in the DUMP_DIR directory
LATEST_DUMP_FILE=$(find "$DUMP_DIR" -maxdepth 1 -name '*.sql' -printf '%T+ %p\n' | sort -r | head -n1 | cut -d" " -f2)

# Check if a .sql dump file was found
if [ -n "$LATEST_DUMP_FILE" ]; then

    # Read the database password from the secret file
    PGPASSWORD=$(cat /run/secrets/db-root-password)
    export PGPASSWORD="$PGPASSWORD"

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
    echo "As no user exists in the database, creating the 'admin' user with priviledges."
    echo "The password for this user is 'admin'"
    # echo "Using the password specified in the db_password.txt file"
    echo "Use this account to access the web administration interface," 
    echo "create you own account, then delete this one."
    # ADMIN_PASSWORD=$(cat /run/secrets/db-password)

    # echo "from django.contrib.auth import get_user_model; User = get_user_model(); User.objects.create_superuser('admin', 'admin@admin.django', '$ADMIN_PASSWORD')" | python /app/alyx/manage.py shell
fi

# Collect static files
echo "Collecting static files..."
pdm run manage.py collectstatic --noinput --clear --verbosity 0

# Start Gunicorn
echo "Starting Gunicorn to serve django alyx..."
exec pdm run gunicorn 'alyx.wsgi' --bind=0.0.0.0:8000


