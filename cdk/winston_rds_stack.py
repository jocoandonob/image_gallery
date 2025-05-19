import aws_cdk as cdk
from aws_cdk import Stack, aws_ec2 as ec2, aws_rds as rds
from constructs import Construct

class WinstonRdsStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, vpc_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Import VPC
        self.vpc = ec2.Vpc.from_lookup(self, "ImportedVpc", vpc_id=vpc_id)
        
        # Create security group
        self.db_security_group = ec2.SecurityGroup(
            self, "DBSecurityGroup",
            vpc=self.vpc,
            description="Security group for RDS PostgreSQL",
            allow_all_outbound=False
        )
        
        # Create RDS instance
        self.db_instance = rds.DatabaseInstance(
            self, "WinstonGalleryDB",
            engine=rds.DatabaseInstanceEngine.postgres(version=rds.PostgresEngineVersion.VER_14),
            instance_type=ec2.InstanceType.of(ec2.InstanceClass.BURSTABLE3, ec2.InstanceSize.SMALL),
            vpc=self.vpc,
            vpc_subnets=ec2.SubnetSelection(subnet_type=ec2.SubnetType.PRIVATE_ISOLATED),
            security_groups=[self.db_security_group],
            removal_policy=cdk.RemovalPolicy.RETAIN,
            deletion_protection=True,
            storage_encrypted=True,
            multi_az=True,
            database_name="winstongallery",
            credentials=rds.Credentials.from_generated_secret("postgres")
        )
        
        # Output
        cdk.CfnOutput(self, "DBEndpoint", value=self.db_instance.db_instance_endpoint_address)
        cdk.CfnOutput(self, "DBSecretArn", value=self.db_instance.secret.secret_arn)