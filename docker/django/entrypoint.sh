#!/bin/bash
echo -n "Django version:" && echo -n $(pdm run python -m django --version) && echo " is installed"

pdm install --prod --no-editable --frozen-lockfile

echo "Applying database migrations..."
pdm run ./src/manage.py migrate # --noinput 

# Collect static files
echo "Collecting static files..."
pdm run ./src/manage.py collectstatic --noinput --clear --verbosity 0

# Restore
echo "Restoring postgres table from backup if any"
pdm run ./src/manage.py dbrestore --noinput

# Start Gunicorn
echo "Starting Gunicorn to serve django alyx..."
exec pdm run gunicorn --reload --reload-engine=inotify 'alyx.base.wsgi' --bind=0.0.0.0:8000 --workers 3