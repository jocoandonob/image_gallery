import os
import psycopg2
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

def add_category_column():
    # Get database URL from environment or use default
    db_url = os.environ.get('DATABASE_URL', 'postgresql://postgres:postgres@localhost:5432/postgres')
    
    # Parse the database URL
    if '@' in db_url:
        auth, host_db = db_url.split('@')
        user_pass = auth.split('://')[1].split(':')
        host_port_db = host_db.split('/')
        host_port = host_port_db[0].split(':')
        
        db_config = {
            'user': user_pass[0],
            'password': user_pass[1],
            'host': host_port[0],
            'port': host_port[1] if len(host_port) > 1 else '5432',
            'database': host_port_db[1]
        }
    else:
        # Default configuration
        db_config = {
            'user': 'postgres',
            'password': 'postgres',
            'host': 'localhost',
            'port': '5432',
            'database': 'postgres'
        }
    
    try:
        # Connect to PostgreSQL
        conn = psycopg2.connect(
            host=db_config['host'],
            user=db_config['user'],
            password=db_config['password'],
            port=db_config['port'],
            database=db_config['database']
        )
        conn.autocommit = True
        cursor = conn.cursor()
        
        # Check if column exists
        cursor.execute("""
        SELECT column_name FROM information_schema.columns 
        WHERE table_name='images' AND column_name='category_id'
        """)
        
        if cursor.fetchone() is None:
            print("Adding category_id column to images table...")
            # Add category_id column
            cursor.execute("""
            ALTER TABLE images 
            ADD COLUMN category_id INTEGER REFERENCES categories(id)
            """)
            print("Column added successfully!")
        else:
            print("category_id column already exists")
        
        # Close connection
        cursor.close()
        conn.close()
        
    except Exception as e:
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    add_category_column()