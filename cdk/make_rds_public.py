import boto3
import time

def make_rds_public():
    # Get RDS instance details
    rds = boto3.client('rds')
    
    # Find the RDS instance
    response = rds.describe_db_instances()
    db_instance = None
    
    for instance in response['DBInstances']:
        if 'winstongallery' in instance['DBInstanceIdentifier'].lower():
            db_instance = instance
            break
    
    if not db_instance:
        print("Could not find RDS instance with 'winstongallery' in the name")
        return False
    
    db_id = db_instance['DBInstanceIdentifier']
    print(f"Found RDS instance: {db_id}")
    
    # Create a snapshot
    snapshot_id = f"winston-snapshot-{int(time.time())}"
    print(f"Creating snapshot: {snapshot_id}")
    
    rds.create_db_snapshot(
        DBSnapshotIdentifier=snapshot_id,
        DBInstanceIdentifier=db_id
    )
    
    # Wait for snapshot to be available
    print("Waiting for snapshot to be available...")
    waiter = rds.get_waiter('db_snapshot_available')
    waiter.wait(
        DBSnapshotIdentifier=snapshot_id,
        WaiterConfig={
            'Delay': 30,
            'MaxAttempts': 60
        }
    )
    print("Snapshot is available")
    
    # Get VPC details
    ec2 = boto3.client('ec2')
    vpc_id = db_instance['DBSubnetGroup']['VpcId']
    
    # Get public subnets
    response = ec2.describe_subnets(
        Filters=[
            {
                'Name': 'vpc-id',
                'Values': [vpc_id]
            },
            {
                'Name': 'map-public-ip-on-launch',
                'Values': ['true']
            }
        ]
    )
    
    if not response['Subnets']:
        print("Could not find public subnets in the VPC")
        return False
    
    public_subnet_ids = [subnet['SubnetId'] for subnet in response['Subnets']]
    print(f"Found public subnets: {public_subnet_ids}")
    
    # Create DB subnet group for public subnets
    subnet_group_name = f"public-subnet-group-{int(time.time())}"
    rds.create_db_subnet_group(
        DBSubnetGroupName=subnet_group_name,
        DBSubnetGroupDescription="Public subnet group for RDS",
        SubnetIds=public_subnet_ids
    )
    print(f"Created DB subnet group: {subnet_group_name}")
    
    # Create security group for public access
    security_group_name = f"rds-public-sg-{int(time.time())}"
    sg_response = ec2.create_security_group(
        GroupName=security_group_name,
        Description="Security group for public RDS access",
        VpcId=vpc_id
    )
    security_group_id = sg_response['GroupId']
    
    # Allow PostgreSQL access from anywhere
    ec2.authorize_security_group_ingress(
        GroupId=security_group_id,
        IpPermissions=[
            {
                'IpProtocol': 'tcp',
                'FromPort': 5432,
                'ToPort': 5432,
                'IpRanges': [
                    {
                        'CidrIp': '0.0.0.0/0',
                        'Description': 'Allow PostgreSQL access from anywhere'
                    }
                ]
            }
        ]
    )
    print(f"Created security group: {security_group_id}")
    
    # Restore from snapshot to a new instance with a shorter name
    new_db_id = f"winston-public-{int(time.time())}"
    print(f"Restoring to new public instance: {new_db_id}")
    
    rds.restore_db_instance_from_db_snapshot(
        DBInstanceIdentifier=new_db_id,
        DBSnapshotIdentifier=snapshot_id,
        DBSubnetGroupName=subnet_group_name,
        PubliclyAccessible=True,
        VpcSecurityGroupIds=[security_group_id],
        MultiAZ=False,  # Set to False to reduce cost
        DBInstanceClass=db_instance['DBInstanceClass']
    )
    
    # Wait for the new instance to be available
    print("Waiting for new instance to be available...")
    waiter = rds.get_waiter('db_instance_available')
    waiter.wait(
        DBInstanceIdentifier=new_db_id,
        WaiterConfig={
            'Delay': 30,
            'MaxAttempts': 60
        }
    )
    
    # Get the new instance details
    response = rds.describe_db_instances(DBInstanceIdentifier=new_db_id)
    new_instance = response['DBInstances'][0]
    endpoint = new_instance['Endpoint']['Address']
    
    print(f"New public RDS instance is available!")
    print(f"Endpoint: {endpoint}")
    print(f"Port: {new_instance['Endpoint']['Port']}")
    
    return {
        'endpoint': endpoint,
        'port': new_instance['Endpoint']['Port'],
        'instance_id': new_db_id
    }

if __name__ == "__main__":
    make_rds_public()
