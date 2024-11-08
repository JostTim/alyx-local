#!/bin/bash

DB_NAME="alyx"

if [ -z "$1" ]; then
    echo "Error: No dump file supplied. Please provide the path to the dump file as an argument."
    exit 1
fi
DUMP_FILE="$1"

echo "Restoring database from $DUMP_FILE..."

DATA_ONLY=false
if [ "$2" == "--data-only" ]; then
    DATA_ONLY=true
    echo "Restoring data only"
else
    echo "Restoring data and database structure"
fi

# Get the directory of the current script
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

PGPASSWORD=$(cat /run/secrets/db-secure-password)
export PGPASSWORD="$PGPASSWORD"

check_exit_status() {
    if [ $? -ne 0 ]; then
        echo "Error: Database restoration command failed. Skipping."
        exit 1
    fi
}

echo -n "Creating database role readaccess if missing..."
psql -h db -U postgres -d "$DB_NAME" -c "DO \$\$
BEGIN
    IF NOT EXISTS (SELECT FROM pg_catalog.pg_roles WHERE rolname = 'readaccess') THEN
        CREATE ROLE readaccess LOGIN;
        GRANT CONNECT ON DATABASE $DB_NAME TO readaccess;
        GRANT USAGE ON SCHEMA public TO readaccess;
        GRANT SELECT ON ALL TABLES IN SCHEMA public TO readaccess;
    END IF;
END
\$\$;"

if [ "$DATA_ONLY" = true ]; then
    psql -h db -U postgres -d "$DB_NAME" -c "SET session_replication_role = replica;"
    check_exit_status

    pg_restore --data-only -h db -U postgres -d "$DB_NAME" < "$DUMP_FILE"
    check_exit_status

    # Re-enable constraints
    psql -h db -U postgres -d "$DB_NAME" -c "SET session_replication_role = origin;"
    check_exit_status

    psql -h db -U postgres -d "$DB_NAME" -f "$SCRIPT_DIR/sql/foreign_key_check.sql" && echo "OK"
    check_exit_status
else 
    pg_restore --clean --if-exists -h db -U postgres -d "$DB_NAME" < "$DUMP_FILE" && echo "OK"
fi