#!/bin/sh

APPS="actions data experiments jobs misc subjects"

# Apply database migrations

echo "Django version installed"
echo python -m django --version


echo "Applying database migrations..."
python manage.py migrate --noinput 

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --clear --verbosity 0

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn 'alyx.wsgi' --bind=0.0.0.0:8000


