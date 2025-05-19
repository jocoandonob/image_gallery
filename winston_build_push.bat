@echo off
echo Building and pushing Docker image to ECR...

REM Get AWS account ID
aws sts get-caller-identity --query "Account" --output text > temp.txt
set /p AWS_ACCOUNT_ID=<temp.txt
del temp.txt

REM Set variables
set AWS_REGION=us-east-1
set ECR_REPO_NAME=winston-gallery-app
set ECR_REPO_URI=%AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com/%ECR_REPO_NAME%

echo AWS Account ID: %AWS_ACCOUNT_ID%
echo ECR Repository URI: %ECR_REPO_URI%

REM Login to ECR
echo Logging in to Amazon ECR...
aws ecr get-login-password --region %AWS_REGION% | docker login --username AWS --password-stdin %AWS_ACCOUNT_ID%.dkr.ecr.%AWS_REGION%.amazonaws.com

REM Build the Docker image
echo Building Docker image...
docker build -t %ECR_REPO_NAME% .

REM Tag the image
echo Tagging image...
docker tag %ECR_REPO_NAME%:latest %ECR_REPO_URI%:latest

REM Push the image to ECR
echo Pushing image to ECR...
docker push %ECR_REPO_URI%:latest

echo Image successfully built and pushed to ECR!
echo You can now deploy your CDK stack with: winston_deploy.bat
pause