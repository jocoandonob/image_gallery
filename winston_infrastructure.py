import aws_cdk as cdk
from aws_cdk import (
    Stack,
    aws_ec2 as ec2,
    aws_ecs as ecs,
    aws_ecr as ecr,
    aws_iam as iam,
    aws_rds as rds,
    aws_s3 as s3,
    aws_elasticloadbalancingv2 as elbv2,
)
from constructs import Construct

class WinstonGalleryStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)

        # Create VPC with isolated subnets for RDS
        vpc = ec2.Vpc(
            self, "WinstonGalleryVPC",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(
                    name="Public",
                    subnet_type=ec2.SubnetType.PUBLIC,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Private",
                    subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS,
                    cidr_mask=24
                ),
                ec2.SubnetConfiguration(
                    name="Isolated",
                    subnet_type=ec2.SubnetType.PRIVATE_ISOLATED,
                    cidr_mask=24
                )
            ]
        )

        # Create S3 bucket for image storage
        image_bucket = s3.Bucket(
            self, "WinstonBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )

        # Create RDS PostgreSQL instance
        db_security_group = ec2.SecurityGroup(
            self, "DBSecurityGroup",
            vpc=vpc,
            description="Security group for RDS PostgreSQL",
            allow_all_outbound=False
        )

        db_instance = rds.DatabaseInstance(
            self, "WinstonGalleryDB",
            engine=rds.DatabaseInstanceEngine.postgres(
                version=rds.PostgresEngineVersion.VER_14
            ),
            instance_type=ec2.InstanceType.of(
                ec2.InstanceClass.BURSTABLE3,
                ec2.InstanceSize.SMALL
            ),
            vpc=vpc,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_ISOLATED
            ),
            security_groups=[db_security_group],
            removal_policy=cdk.RemovalPolicy.RETAIN,
            deletion_protection=True,
            storage_encrypted=True,
            multi_az=True,
            database_name="winstongallery",
            credentials=rds.Credentials.from_generated_secret("postgres")
        )

        # Create ECS cluster
        cluster = ecs.Cluster(
            self, "WinstonGalleryCluster",
            vpc=vpc
        )

        # Create ECS task execution role
        execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy")
            ]
        )

        # Create ECS task role with least privilege
        task_role = iam.Role(
            self, "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )

        # Grant task role access to S3 bucket with least privilege
        image_bucket.grant_read_write(task_role)

        # Create security group for ECS tasks
        task_security_group = ec2.SecurityGroup(
            self, "TaskSecurityGroup",
            vpc=vpc,
            description="Security group for ECS tasks",
            allow_all_outbound=True
        )

        # Allow ECS tasks to connect to RDS
        db_security_group.add_ingress_rule(
            task_security_group,
            ec2.Port.tcp(5432),
            "Allow access from ECS tasks"
        )

        # Create ECS Fargate service
        task_definition = ecs.FargateTaskDefinition(
            self, "TaskDef",
            execution_role=execution_role,
            task_role=task_role,
            cpu=256,
            memory_limit_mib=512
        )

        # Create ECR repository for the application
        repository = ecr.Repository(
            self, "WinstonGalleryRepo",
            repository_name="winston-gallery-app",
            removal_policy=cdk.RemovalPolicy.RETAIN,
        )
        
        # Add container to task definition
        container = task_definition.add_container(
            "WinstonGalleryApp",
            # Use the ECR repository - you'll need to build and push your image to this repo
            image=ecs.ContainerImage.from_ecr_repository(repository),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="winston-gallery"),
            environment={
                "S3_BUCKET": image_bucket.bucket_name,
                "DB_SECRET_ARN": db_instance.secret.secret_arn,
                "AWS_REGION": self.region
            }
        )

        container.add_port_mappings(
            ecs.PortMapping(container_port=5000)
        )

        # Grant task role access to read DB secret
        db_instance.secret.grant_read(task_role)

        # Create security group for ALB
        alb_security_group = ec2.SecurityGroup(
            self, "ALBSecurityGroup",
            vpc=vpc,
            description="Security group for ALB",
            allow_all_outbound=True
        )
        
        # Allow inbound HTTP traffic to ALB
        alb_security_group.add_ingress_rule(
            ec2.Peer.any_ipv4(),
            ec2.Port.tcp(80),
            "Allow HTTP traffic"
        )
        
        # Create Application Load Balancer
        alb = elbv2.ApplicationLoadBalancer(
            self, "WinstonGalleryALB",
            vpc=vpc,
            internet_facing=True,
            security_group=alb_security_group,
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PUBLIC
            )
        )
        
        # Create ALB listener
        listener = alb.add_listener(
            "HttpListener",
            port=80,
            open=True
        )
        
        # Create Fargate service with ALB integration
        service = ecs.FargateService(
            self, "Service",
            cluster=cluster,
            task_definition=task_definition,
            desired_count=2,
            security_groups=[task_security_group],
            vpc_subnets=ec2.SubnetSelection(
                subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS
            )
        )
        
        # Register ECS service as target for ALB
        listener.add_targets(
            "ECSTarget",
            port=5000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[service],
            health_check=elbv2.HealthCheck(
                path="/",
                interval=cdk.Duration.seconds(60),
                timeout=cdk.Duration.seconds(5)
            )
        )

        # Output the S3 bucket name
        cdk.CfnOutput(
            self, "BucketName",
            value=image_bucket.bucket_name
        )

        # Output the DB endpoint
        cdk.CfnOutput(
            self, "DBEndpoint",
            value=db_instance.db_instance_endpoint_address
        )
        
        # Output the ALB DNS name
        cdk.CfnOutput(
            self, "LoadBalancerDNS",
            value=alb.load_balancer_dns_name
        )

app = cdk.App()
env = cdk.Environment(
    account=app.node.try_get_context('account') or '040170486841',  # Your AWS account ID
    region=app.node.try_get_context('region') or 'us-east-1'
)
WinstonGalleryStack(app, "WinstonGalleryStack", env=env)
try:
    assembly = app.synth()
    print(f"Assembly directory: {assembly.directory}")
except Exception as e:
    print(f"Error during synthesis: {str(e)}")
    import traceback
    traceback.print_exc()