#!/bin/bash
set -e

# Wait for PostgreSQL to be ready
echo "Waiting for PostgreSQL..."
while ! nc -z db 5432; do
  sleep 1
done
echo "PostgreSQL started"

# Create tables and admin user
python << EOF
import os
import sys
from app import app, db, User
from werkzeug.security import generate_password_hash
from sqlalchemy.exc import SQLAlchemyError

try:
    with app.app_context():
        # Check database connection
        try:
            db.engine.connect()
            print("Database connection successful")
        except Exception as e:
            print(f"Database connection failed: {e}")
            sys.exit(1)
            
        # Create tables
        db.create_all()
        print("Database tables created")
        
        # Create admin user if not exists
        admin = User.query.filter_by(username='admin').first()
        if not admin:
            admin = User(username='admin')
            admin.password_hash = generate_password_hash('admin')
            db.session.add(admin)
            db.session.commit()
            print("Admin user created")
        else:
            print("Admin user already exists")
except SQLAlchemyError as e:
    print(f"Database error: {e}")
    sys.exit(1)
except Exception as e:
    print(f"Error: {e}")
    sys.exit(1)
EOF

# Start the application
exec gunicorn --bind 0.0.0.0:5000 --log-level debug app:app