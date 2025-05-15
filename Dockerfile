FROM python:3.11-slim

WORKDIR /app

# Install dependencies
RUN apt-get update && apt-get install -y netcat-traditional && rm -rf /var/lib/apt/lists/*
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY . .

# Create upload directory
RUN mkdir -p static/uploads

# Make entrypoint script executable
RUN chmod +x entrypoint.sh

# Expose port
EXPOSE 5000

# Set environment variables
ENV FLASK_APP=app.py
ENV FLASK_ENV=production
ENV DATABASE_URL=postgresql://postgres:postgres@db:5432/postgres

# Run the application
ENTRYPOINT ["./entrypoint.sh"]