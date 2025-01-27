#!/bin/sh

echo "Waiting for database to be ready..."
until python -c "import psycopg2; psycopg2.connect(dbname='$POSTGRES_DB', user='$POSTGRES_USER', password='$POSTGRES_PASSWORD', host='$POSTGRES_HOST', port='$POSTGRES_PORT')"; do
  echo "Waiting for PostgreSQL to be available..."
  sleep 1
done
echo "Database is ready!"

echo "Applying database migrations..."
python manage.py makemigrations --noinput
python manage.py migrate --noinput

echo "Collecting static files..."
python manage.py collectstatic --noinput --clear

# Pokreni Celery samo kada je sve spremno
echo "Starting Celery workers..."
celery -A chesshub_project worker --loglevel=info --detach

echo "Starting application server..."
exec "$@"
