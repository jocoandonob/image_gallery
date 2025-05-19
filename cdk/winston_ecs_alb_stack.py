import aws_cdk as cdk
from aws_cdk import Stack, aws_ec2 as ec2, aws_ecs as ecs, aws_iam as iam, aws_elasticloadbalancingv2 as elbv2
from constructs import Construct

class WinstonEcsAlbStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc, repository_uri: str, bucket_name: str, db_secret_arn: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Use VPC directly
        self.vpc = vpc
        
        # Create ECS cluster
        self.cluster = ecs.Cluster(self, "WinstonGalleryCluster", vpc=self.vpc)
        
        # Create roles
        execution_role = iam.Role(
            self, "TaskExecutionRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com"),
            managed_policies=[
                iam.ManagedPolicy.from_aws_managed_policy_name("service-role/AmazonECSTaskExecutionRolePolicy"), 
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonECS_FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonS3FullAccess"),
                iam.ManagedPolicy.from_aws_managed_policy_name("AmazonRDSFullAccess"),
            ]
        )
        
        task_role = iam.Role(
            self, "TaskRole",
            assumed_by=iam.ServicePrincipal("ecs-tasks.amazonaws.com")
        )
        
        # Grant permissions
        task_role.add_to_policy(iam.PolicyStatement(
            actions=["s3:GetObject", "s3:PutObject", "s3:ListBucket"],
            resources=[f"arn:aws:s3:::{bucket_name}", f"arn:aws:s3:::{bucket_name}/*"]
        ))
        
        task_role.add_to_policy(iam.PolicyStatement(
            actions=["secretsmanager:GetSecretValue"],
            resources=[db_secret_arn]
        ))
        
        # Create security groups
        task_security_group = ec2.SecurityGroup(
            self, "TaskSecurityGroup",
            vpc=self.vpc,
            description="Security group for ECS tasks",
            allow_all_outbound=True
        )
        
        alb_security_group = ec2.SecurityGroup(
            self, "ALBSecurityGroup",
            vpc=self.vpc,
            description="Security group for ALB",
            allow_all_outbound=True
        )
        
        alb_security_group.add_ingress_rule(ec2.Peer.any_ipv4(), ec2.Port.tcp(80), "Allow HTTP traffic")
        
        # Create task definition
        task_definition = ecs.FargateTaskDefinition(
            self, "TaskDef",
            execution_role=execution_role,
            task_role=task_role,
            cpu=256,
            memory_limit_mib=512
        )
        
        container = task_definition.add_container(
            "WinstonGalleryApp",
            image=ecs.ContainerImage.from_registry(repository_uri + ":latest"),
            logging=ecs.LogDrivers.aws_logs(stream_prefix="winston-gallery"),
            environment={
                "S3_BUCKET": bucket_name,
                "DB_SECRET_ARN": db_secret_arn,
                "AWS_REGION": self.region
            }
        )
        
        container.add_port_mappings(ecs.PortMapping(container_port=5000))
        
        # Create ALB
        self.alb = elbv2.ApplicationLoadBalancer(
            self, "WinstonGalleryALB",
            vpc=self.vpc,
            internet_facing=True,
            security_group=alb_security_group,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PUBLIC)
        )
        
        listener = self.alb.add_listener("HttpListener", port=80, open=True)
        
        # Create service
        service = ecs.FargateService(
            self, "Service",
            cluster=self.cluster,
            task_definition=task_definition,
            desired_count=2,
            security_groups=[task_security_group],
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS)
        )
        
        # Register targets
        listener.add_targets(
            "ECSTarget",
            port=5000,
            protocol=elbv2.ApplicationProtocol.HTTP,
            targets=[service],
            health_check=elbv2.HealthCheck(path="/", interval=cdk.Duration.seconds(60), timeout=cdk.Duration.seconds(5))
        )
        
        # Output
        cdk.CfnOutput(self, "LoadBalancerDNS", value=self.alb.load_balancer_dns_name)