#!/bin/bash
set -e

echo "Starting Docker entrypoint script..."

# Initialize the database
echo "Initializing database..."
python init-db.py

# Start the application
echo "Starting Flask application..."
exec python app.py