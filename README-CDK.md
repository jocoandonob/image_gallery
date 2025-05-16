# Image Gallery Infrastructure

This project uses AWS CDK to provision infrastructure for the Image Gallery application with secure IAM roles between ECS, RDS, and S3.

## Prerequisites

- AWS CLI configured with appropriate credentials
- Python 3.6 or later
- Node.js 14.x or later

## Setup

1. Install the required dependencies:

```bash
pip install -r requirements-cdk.txt
npm install -g aws-cdk
```

2. Bootstrap your AWS environment (if not already done):

```bash
cdk bootstrap
```

3. Deploy the stack:

```bash
cdk deploy
```

## Infrastructure Components

- **VPC**: Isolated network with public, private, and isolated subnets
- **ECS Cluster**: Runs the containerized application
- **RDS PostgreSQL**: Database for storing application data
- **S3 Bucket**: Storage for image files
- **IAM Roles**: Least-privilege access between services

## Security Features

- Private subnets for RDS with security group restrictions
- Task execution role with minimal permissions
- Task role with specific permissions for S3 and RDS
- S3 bucket with server-side encryption and blocked public access
- RDS with encryption at rest and in a private subnet
- Secrets management for database credentials