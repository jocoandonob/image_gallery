import aws_cdk as cdk
from aws_cdk import Stack, aws_ecr as ecr
from constructs import Construct

class WinstonEcrStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create ECR repository
        self.repository = ecr.Repository(
            self, "WinstonGalleryRepo",
            repository_name="winston-gallery-app",
            removal_policy=cdk.RemovalPolicy.RETAIN
        )
        
        # Output
        cdk.CfnOutput(self, "RepositoryUri", value=self.repository.repository_uri)