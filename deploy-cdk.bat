@echo off
echo Activating CDK environment...
call cdk-venv\Scripts\activate.bat
echo Running CDK deployment...
cdk deploy --require-approval never --verbose
if %ERRORLEVEL% NEQ 0 (
    echo Deployment failed with error code %ERRORLEVEL%
    echo Trying with admin permissions...
    cdk deploy --require-approval never --verbose --role-arn arn:aws:iam::040170486841:role/cdk-hnb659fds-cfn-exec-role-040170486841-us-east-1
)