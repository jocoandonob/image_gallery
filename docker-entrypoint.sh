#!/bin/sh
set -e

echo "Starting Docker entrypoint script..."

# Check if DB_SECRET_ARN is provided (AWS environment)
if [ -n "$DB_SECRET_ARN" ]; then
    echo "Running in AWS environment, retrieving database credentials from Secrets Manager"
    
    # Install AWS CLI if not already installed
    if ! command -v aws &> /dev/null; then
        echo "Installing AWS CLI..."
        pip install --no-cache-dir awscli
    fi
    
    # Get database credentials from Secrets Manager
    DB_SECRET=$(aws secretsmanager get-secret-value --secret-id $DB_SECRET_ARN --query SecretString --output text)
    
    # Parse the JSON and set environment variables
    export DATABASE_URL="postgresql://$(echo $DB_SECRET | grep -o '"username":"[^"]*' | cut -d'"' -f4):$(echo $DB_SECRET | grep -o '"password":"[^"]*' | cut -d'"' -f4)@$(echo $DB_SECRET | grep -o '"host":"[^"]*' | cut -d'"' -f4):$(echo $DB_SECRET | grep -o '"port":[^,]*' | cut -d':' -f2)/$(echo $DB_SECRET | grep -o '"dbname":"[^"]*' | cut -d'"' -f4)"
    
    echo "Database connection configured from Secrets Manager"
else
    echo "Running in local environment, using DATABASE_URL from environment variables"
fi

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
DB_HOST=$(echo $DATABASE_URL | cut -d'@' -f2 | cut -d':' -f1)
DB_PORT=$(echo $DATABASE_URL | cut -d':' -f3 | cut -d'/' -f1)

# Try to connect to PostgreSQL
for i in $(seq 1 30); do
    nc -z $DB_HOST $DB_PORT && break
    echo "Waiting for PostgreSQL to start... ($i/30)"
    sleep 1
done

if [ $i -eq 30 ]; then
    echo "PostgreSQL did not start in time"
    exit 1
fi

echo "PostgreSQL started"

# Initialize the database
python init-db.py

# Start the application with gunicorn
echo "Starting application..."
exec gunicorn -b 0.0.0.0:5000 app:app