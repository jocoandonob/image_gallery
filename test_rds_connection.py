import boto3
import json
import psycopg2

def test_rds_connection():
    # Connect directly to the new public RDS instance
    host = "winston-public-1747647416.cpihf2p85fkq.us-east-1.rds.amazonaws.com"
    
    # Get the secret from the original RDS instance (credentials should be the same)
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
    
    print(f"Found DB Secret ARN: {secret_arn}")
    
    # Get the secret value
    sm = boto3.client('secretsmanager')
    response = sm.get_secret_value(SecretId=secret_arn)
    secret = json.loads(response['SecretString'])
    
    print(f"Using credentials from secret for host: {host}")
    
    # Connect to the database
    try:
        conn = psycopg2.connect(
            host=host,
            user=secret['username'],
            password=secret['password'],
            dbname=secret['dbname'],
            port=secret['port']
        )
        
        cursor = conn.cursor()
        cursor.execute("SELECT 1 AS connection_test")
        result = cursor.fetchone()
        
        print(f"Connection successful! Result: {result[0]}")

        
        print(f"host: {host}")
        print(f"secret['username']: {secret['username']}")
        print(f"secret['password']: {secret['password']}")
        print(f"secret['dbname']: {secret['dbname']}")
        print(f"secret['port']: {secret['port']}")
        
        # Create tables if they don't exist
        cursor.execute("""
        CREATE TABLE IF NOT EXISTS users (
            id SERIAL PRIMARY KEY,
            username VARCHAR(80) UNIQUE NOT NULL,
            password_hash VARCHAR(255) NOT NULL
        )
        """)
        
        # Check if tables were created
        cursor.execute("SELECT COUNT(*) FROM users")
        user_count = cursor.fetchone()[0]
        print(f"Users table exists with {user_count} records")
        
        conn.commit()
        conn.close()
        return True
        
    except Exception as e:
        print(f"Connection failed: {str(e)}")
        return False

if __name__ == "__main__":
    if test_rds_connection():
        print("RDS database is working correctly!")
    else:
        print("Failed to connect to RDS database.")
