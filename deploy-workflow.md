# Deployment Workflow

Follow these steps to deploy your Image Gallery application to AWS:

## 1. Bootstrap CDK (First time only)

```
bootstrap-cdk.bat
```

## 2. Deploy the CDK Stack

```
deploy-cdk.bat
```

This creates:
- ECR repository
- RDS PostgreSQL database
- S3 bucket
- ECS cluster and other infrastructure

## 3. Build and Push Docker Image

```
build-and-push.bat
```

This builds your Docker image and pushes it to the ECR repository.

## 4. Update ECS Service

After pushing a new image, you need to update the ECS service:

```
aws ecs update-service --cluster ImageGalleryCluster --service ImageGalleryStack-Service --force-new-deployment
```

## 5. Access Your Application

Find your application URL in the AWS Console:
1. Go to CloudFormation → Stacks → ImageGalleryStack → Outputs
2. Look for the "LoadBalancerDNS" output value

## Troubleshooting

If you encounter issues:
1. Check CloudWatch Logs for container logs
2. Verify security group settings
3. Check that the database is accessible from the ECS tasks
4. Ensure your Docker image is built correctly and pushed to ECR