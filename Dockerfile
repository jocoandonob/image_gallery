FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && \
    apt-get install -y netcat-traditional curl unzip && \
    rm -rf /var/lib/apt/lists/*

# Install AWS CLI
RUN curl "https://awscli.amazonaws.com/awscli-exe-linux-x86_64.zip" -o "awscliv2.zip" && \
    unzip awscliv2.zip && \
    ./aws/install && \
    rm -rf aws awscliv2.zip

# Copy requirements and install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt gunicorn

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p static/uploads

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV PYTHONUNBUFFERED=1

# Create entrypoint script
RUN echo '#!/bin/sh\n\
set -e\n\
\n\
echo "Starting Docker entrypoint script..."\n\
\n\
# Get database credentials from Secrets Manager\n\
if [ -n "$DB_SECRET_ARN" ]; then\n\
    echo "Getting database credentials from Secrets Manager"\n\
    DB_SECRET=$(aws secretsmanager get-secret-value --secret-id $DB_SECRET_ARN --query SecretString --output text)\n\
    export DB_USER=$(echo $DB_SECRET | python -c "import sys, json; print(json.load(sys.stdin)[\"username\"])")\n\
    export DB_PASSWORD=$(echo $DB_SECRET | python -c "import sys, json; print(json.load(sys.stdin)[\"password\"])")\n\
    export DB_HOST=$(echo $DB_SECRET | python -c "import sys, json; print(json.load(sys.stdin)[\"host\"])")\n\
    export DB_PORT=$(echo $DB_SECRET | python -c "import sys, json; print(json.load(sys.stdin)[\"port\"])")\n\
    export DB_NAME=$(echo $DB_SECRET | python -c "import sys, json; print(json.load(sys.stdin)[\"dbname\"])")\n\
    export DATABASE_URL="postgresql://$DB_USER:$DB_PASSWORD@$DB_HOST:$DB_PORT/$DB_NAME"\n\
fi\n\
\n\
# Get application secrets from Secrets Manager\n\
if [ -n "$APP_SECRET_ARN" ]; then\n\
    echo "Getting application secrets from Secrets Manager"\n\
    APP_SECRET=$(aws secretsmanager get-secret-value --secret-id $APP_SECRET_ARN --query SecretString --output text)\n\
    export SECRET_KEY=$(echo $APP_SECRET | python -c "import sys, json; print(json.load(sys.stdin)[\"SECRET_KEY\"])")\n\
    export FLASK_ENV=$(echo $APP_SECRET | python -c "import sys, json; print(json.load(sys.stdin)[\"FLASK_ENV\"])")\n\
fi\n\
\n\
echo "Starting application..."\n\
exec gunicorn --bind 0.0.0.0:5000 app:app\n\
' > /app/docker-entrypoint.sh

RUN chmod +x /app/docker-entrypoint.sh

# Run the application
ENTRYPOINT ["/app/docker-entrypoint.sh"]
