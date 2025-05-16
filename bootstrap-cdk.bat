@echo off
echo Bootstrapping AWS CDK environment...
call cdk-venv\Scripts\activate.bat

echo Using admin permissions for bootstrap...
cdk bootstrap aws://040170486841/us-east-1 --cloudformation-execution-policies "arn:aws:iam::aws:policy/AdministratorAccess" --trust 040170486841

if %ERRORLEVEL% NEQ 0 (
    echo Bootstrap failed with error code %ERRORLEVEL%
    echo You may need to run with admin privileges or check your AWS credentials
    pause
    exit /b %ERRORLEVEL%
)
echo Bootstrap completed successfully!
echo You can now run deploy-cdk.bat to deploy your stack