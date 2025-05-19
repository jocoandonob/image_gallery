# init_db.py
import os
import psycopg2
import json
import boto3

def init_db():
    # Get connection details
    host = "winston-public-1747647416.cpihf2p85fkq.us-east-1.rds.amazonaws.com"
    
    # Get the secret from the original RDS instance
    cfn = boto3.client('cloudformation')
    response = cfn.describe_stacks(StackName='WinstonGalleryRdsStack')
    secret_arn = None
    
    for output in response['Stacks'][0]['Outputs']:
        if output['OutputKey'] == 'DBSecretArn':
            secret_arn = output['OutputValue']
            break
    
    if not secret_arn:
        print("Could not find DBSecretArn in CloudFormation outputs")
        return False
    
    # Get the secret value
    sm = boto3.client('secretsmanager')
    response = sm.get_secret_value(SecretId=secret_arn)
    secret = json.loads(response['SecretString'])
    
    # Connect to the database
    conn = psycopg2.connect(
        host=host,
        user=secret['username'],
        password=secret['password'],
        dbname=secret['dbname'],
        port=secret['port']
    )
    
    # Create tables
    with conn.cursor() as cursor:
        # Users table (already exists)
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        )
        """)
        
        # Categories table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS categories (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL
        )
        """)
        
        # Tags table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS tags (
            id SERIAL PRIMARY KEY,
            name VARCHAR(50) UNIQUE NOT NULL
        )
        """)
        
        # Images table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS images (
            id SERIAL PRIMARY KEY,
            filename VARCHAR(255) NOT NULL,
            title VARCHAR(100) NOT NULL,
            description TEXT,
            upload_date TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            user_id INTEGER REFERENCES users(id) NOT NULL,
            category_id INTEGER REFERENCES categories(id)
        )
        """)
        
        # Image-Tags association table
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS image_tags (
            image_id INTEGER REFERENCES images(id) ON DELETE CASCADE,
            tag_id INTEGER REFERENCES tags(id) ON DELETE CASCADE,
            PRIMARY KEY (image_id, tag_id)
        )
        """)
        
        # Add some default categories
        cursor.execute("INSERT INTO categories (name) VALUES ('Nature') ON CONFLICT (name) DO NOTHING")
        cursor.execute("INSERT INTO categories (name) VALUES ('Architecture') ON CONFLICT (name) DO NOTHING")
        cursor.execute("INSERT INTO categories (name) VALUES ('People') ON CONFLICT (name) DO NOTHING")
        cursor.execute("INSERT INTO categories (name) VALUES ('Animals') ON CONFLICT (name) DO NOTHING")
        
        # Add some default tags
        cursor.execute("INSERT INTO tags (name) VALUES ('sunset') ON CONFLICT (name) DO NOTHING")
        cursor.execute("INSERT INTO tags (name) VALUES ('beach') ON CONFLICT (name) DO NOTHING")
        cursor.execute("INSERT INTO tags (name) VALUES ('mountain') ON CONFLICT (name) DO NOTHING")
        cursor.execute("INSERT INTO tags (name) VALUES ('city') ON CONFLICT (name) DO NOTHING")
        
        conn.commit()
        
    print("Database initialized successfully!")
    conn.close()

if __name__ == "__main__":
    init_db()
