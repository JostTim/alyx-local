#!/bin/bash
DUMP_DIR="/data"

# Find the latest .sql file in the DUMP_DIR directory
LATEST_DUMP_FILE=$(find "$DUMP_DIR" -maxdepth 1 -name '*.sql' -printf '%T+ %p\n' | sort -r | head -n1 | cut -d" " -f2)

# Check if a .sql dump file was found
if [ -n "$LATEST_DUMP_FILE" ]; then
    
    ./scripts/restore_db.sh "$LATEST_DUMP_FILE"
else
    echo "No SQL dump file found in $DUMP_DIR. Skipping restore."
    echo "As no user exists in the database, creating the 'admin' user with priviledges. \
    The password for this user is 'admin' \
    Use this account to access the web administration interface, \
    create you own account, then delete this one."
fi