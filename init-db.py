import os
import time
import psycopg2
from psycopg2.extensions import ISOLATION_LEVEL_AUTOCOMMIT
from werkzeug.security import generate_password_hash
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def init_database():
    # Get database URL from environment or use default
    db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@db:5432/postgres')
    
    # Parse the database URL
    if '@' in db_url:
        auth, host_db = db_url.split('@')
        user_pass = auth.split('://')[1].split(':')
        host_port_db = host_db.split('/')
        
        db_config = {
            'user': user_pass[0],
            'password': user_pass[1],
            'host': host_port_db[0].split(':')[0],
            'port': host_port_db[0].split(':')[1] if ':' in host_port_db[0] else '5432',
            'database': host_port_db[1]
        }
    else:
        # Default configuration
        db_config = {
            'user': 'postgres',
            'password': 'postgres',
            'host': 'db',
            'port': '5432',
            'database': 'postgres'
        }
    
    print(f"Connecting to PostgreSQL at {db_config['host']}:{db_config['port']} as {db_config['user']}")
    
    # Wait for PostgreSQL to be ready
    max_retries = 30
    retry_interval = 2
    
    for i in range(max_retries):
        try:
            conn = psycopg2.connect(
                host=db_config['host'],
                user=db_config['user'],
                password=db_config['password'],
                port=db_config['port'],
                database=db_config['database']
            )
            conn.set_isolation_level(ISOLATION_LEVEL_AUTOCOMMIT)
            print("Successfully connected to PostgreSQL")
            break
        except psycopg2.OperationalError as e:
            if i < max_retries - 1:
                print(f"Waiting for PostgreSQL to start... ({i+1}/{max_retries})")
                time.sleep(retry_interval)
            else:
                print(f"Failed to connect to PostgreSQL after {max_retries} attempts: {e}")
                return False
    
    try:
        cursor = conn.cursor()
        
        # Drop existing tables to ensure clean state
        print("Dropping existing tables...")
        cursor.execute("""
        DROP TABLE IF EXISTS image_tags CASCADE;
        DROP TABLE IF EXISTS images CASCADE;
        DROP TABLE IF EXISTS tags CASCADE;
        DROP TABLE IF EXISTS users CASCADE;
        """)
        
        # Create tables
        print("Creating tables...")
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER REFERENCES users(id) NOT NULL
        );
        """)
        
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_tags (
            image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (image_id, tag_id)
        );
        """)
        
        # Create admin user
        print("Creating admin user...")
        password_hash = generate_password_hash('admin')
        cursor.execute("""
        INSERT INTO users (username, password_hash) 
        VALUES (%s, %s)
        ON CONFLICT (username) DO UPDATE 
        SET password_hash = EXCLUDED.password_hash
        """, ('admin', password_hash))
        
        print("Database initialization completed successfully!")
        
        # Close connection
        cursor.close()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Error initializing database: {str(e)}")
        return False

if __name__ == "__main__":
    init_database()