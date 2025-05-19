# Winston Gallery Deployment Guide

Follow these steps to deploy the Winston Gallery application to AWS in stages:

## Step 1: Deploy VPC and S3 Bucket

```bash
cdk deploy WinstonGalleryVpcS3Stack
```

After deployment, note the outputs:
- VpcId
- BucketName

## Step 2: Deploy ECR Repository

```bash
cdk deploy WinstonGalleryEcrStack
```

After deployment, note the output:
- RepositoryUri

## Step 3: Build and Push Docker Image

```bash
winston_build_push.bat
```

## Step 4: Deploy RDS Database

```bash
cdk deploy WinstonGalleryRdsStack --context vpc_id=YOUR_VPC_ID
```

Replace YOUR_VPC_ID with the VpcId from Step 1.

After deployment, note the outputs:
- DBEndpoint
- DBSecretArn

## Step 5: Deploy ECS and ALB

```bash
cdk deploy WinstonGalleryEcsAlbStack --context vpc_id=YOUR_VPC_ID --context repository_uri=YOUR_REPO_URI --context bucket_name=YOUR_BUCKET_NAME --context db_secret_arn=YOUR_DB_SECRET_ARN
```

Replace the placeholders with values from previous steps.

After deployment, note the output:
- LoadBalancerDNS - This is the URL to access your application

## Troubleshooting

If you encounter issues:
1. Check CloudWatch Logs for container logs
2. Verify security group settings
3. Check that the database is accessible from the ECS tasks
4. Ensure your Docker image is built correctly and pushed to ECR