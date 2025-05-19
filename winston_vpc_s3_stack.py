import aws_cdk as cdk
from aws_cdk import Stack, aws_ec2 as ec2, aws_s3 as s3
from constructs import Construct

class WinstonVpcS3Stack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create VPC
        self.vpc = ec2.Vpc(
            self, "WinstonGalleryVPC",
            max_azs=2,
            subnet_configuration=[
                ec2.SubnetConfiguration(name="Public", subnet_type=ec2.SubnetType.PUBLIC, cidr_mask=24),
                ec2.SubnetConfiguration(name="Private", subnet_type=ec2.SubnetType.PRIVATE_WITH_EGRESS, cidr_mask=24),
                ec2.SubnetConfiguration(name="Isolated", subnet_type=ec2.SubnetType.PRIVATE_ISOLATED, cidr_mask=24)
            ]
        )
        
        # Create S3 bucket
        self.image_bucket = s3.Bucket(
            self, "WinstonBucket",
            encryption=s3.BucketEncryption.S3_MANAGED,
            block_public_access=s3.BlockPublicAccess.BLOCK_ALL,
            enforce_ssl=True,
            removal_policy=cdk.RemovalPolicy.RETAIN
        )
        
        # Outputs
        cdk.CfnOutput(self, "VpcId", value=self.vpc.vpc_id)
        cdk.CfnOutput(self, "BucketName", value=self.image_bucket.bucket_name)

app = cdk.App()
env = cdk.Environment(account='040170486841', region='us-east-1')
WinstonVpcS3Stack(app, "WinstonGalleryVpcS3Stack", env=env)
app.synth()