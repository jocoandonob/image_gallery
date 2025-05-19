# Winston Gallery Application

This application uses AWS infrastructure deployed with CDK to host an image gallery application.

## Infrastructure Components

- **VPC** with public, private, and isolated subnets
- **S3 Bucket** for storing images
- **RDS PostgreSQL** database for metadata
- **ECR Repository** for Docker images
- **ECS Fargate** for running containers
- **Application Load Balancer** for routing traffic

## Deployment Instructions

See [winston_deploy.md](winston_deploy.md) for step-by-step deployment instructions.

## Files

- `winston_vpc_s3_stack.py` - VPC and S3 bucket infrastructure
- `winston_ecr_stack.py` - ECR repository infrastructure
- `winston_rds_stack.py` - RDS database infrastructure
- `winston_ecs_alb_stack.py` - ECS and ALB infrastructure
- `winston_infrastructure.py` - Complete infrastructure in a single stack (alternative)
- `winston_build_push.bat` - Script to build and push Docker image
- `winston_deploy.md` - Deployment guide