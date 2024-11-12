#!/bin/bash
echo -n "Django version:" && echo -n $(pdm run python -m django --version) && echo " is installed"

./restore.sh

echo "Applying database migrations..."
pdm run manage.py migrate --noinput 

# Collect static files
echo "Collecting static files..."
pdm run manage.py collectstatic --noinput --clear --verbosity 0

# Start Gunicorn
echo "Starting Gunicorn to serve django alyx..."
exec pdm run gunicorn 'alyx.wsgi' --bind=0.0.0.0:8000