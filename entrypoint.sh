#!/bin/sh
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL started"

# Initialize the database
python init-db.py

# Start the application
exec gunicorn -b 0.0.0.0:5000 app:app