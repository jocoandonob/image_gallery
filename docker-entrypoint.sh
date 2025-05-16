#!/bin/bash
set -e

echo "Starting Docker entrypoint script..."

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL started"

# Initialize the database with the correct schema
python << EOF
import os
import sys
from app import app, db, User, Category, Tag, Image
from werkzeug.security import generate_password_hash
from sqlalchemy import text

try:
    with app.app_context():
        # Check if tables exist and drop them
        db.drop_all()
        
        # Create all tables with updated schema
        db.create_all()
        print("Database tables created successfully")
        
        # Create default categories
        default_categories = ['Nature', 'Architecture', 'People', 'Animals', 'Travel', 'Food', 'Art', 'Other']
        for cat_name in default_categories:
            db.session.add(Category(name=cat_name))
        
        # Create admin user
        admin = User(username='admin')
        admin.password_hash = generate_password_hash('admin')
        db.session.add(admin)
        
        db.session.commit()
        print("Default data created successfully")
except Exception as e:
    print(f"Database initialization error: {str(e)}")
    sys.exit(1)
EOF

# Start the application
exec python app.py