#!/bin/bash

# Define the database name and dump file name
DB_NAME="alyx_db"

CURRENT_DATETIME=$(date +"%Y-%m-%dT%H_%M_%S")
DUMP_ROOT="/data"

DUMP_FILE="${DUMP_ROOT}/dump_${CURRENT_DATETIME}.sql"

# Perform the database dump as the root user
sudo pg_dump -U postgres -w -F c -b -v -f "$DUMP_FILE" "$DB_NAME"