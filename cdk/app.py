#!/usr/bin/env python3
import aws_cdk as cdk
from winston_vpc_s3_stack import WinstonVpcS3Stack
from winston_ecr_stack import WinstonEcrStack
from winston_rds_stack import WinstonRdsStack
from winston_ecs_alb_stack import WinstonEcsAlbStack

app = cdk.App()
env = cdk.Environment(account='040170486841', region='us-east-1')

# Deploy VPC and S3
vpc_s3_stack = WinstonVpcS3Stack(app, "WinstonGalleryVpcS3Stack", env=env)

# Deploy ECR
ecr_stack = WinstonEcrStack(app, "WinstonGalleryEcrStack", env=env)

# Deploy RDS with VPC reference
rds_stack = WinstonRdsStack(app, "WinstonGalleryRdsStack", 
                           vpc=vpc_s3_stack.vpc,  # Pass the VPC object directly
                           env=env)

# Deploy ECS and ALB
ecs_alb_stack = WinstonEcsAlbStack(app, "WinstonGalleryEcsAlbStack",
                                  vpc=vpc_s3_stack.vpc,  # Pass the VPC object directly
                                  repository_uri=ecr_stack.repository.repository_uri,
                                  bucket_name=vpc_s3_stack.image_bucket.bucket_name,
                                  db_secret_arn=rds_stack.db_instance.secret.secret_arn,
                                  env=env)

app.synth()
