#!/bin/sh

# Apply database migrations
echo "Applying database migrations..."
python manage.py migrate --noinput

# Collect static files
echo "Collecting static files..."
python manage.py collectstatic --noinput --verbosity 0

# Start Gunicorn
echo "Starting Gunicorn..."
exec gunicorn 'alyx.wsgi' --bind=0.0.0.0:8000