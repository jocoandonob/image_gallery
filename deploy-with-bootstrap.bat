@echo off
echo Running CDK bootstrap and deploy...

echo Step 1: Activating virtual environment
call cdk-venv\Scripts\activate.bat

echo Step 2: Bootstrapping AWS environment
cdk bootstrap aws://040170486841/us-east-1 --cloudformation-execution-policies "arn:aws:iam::aws:policy/AdministratorAccess" --trust 040170486841
if %ERRORLEVEL% NEQ 0 (
    echo Bootstrap failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo Step 3: Deploying stack
cdk deploy --require-approval never
if %ERRORLEVEL% NEQ 0 (
    echo Deployment failed with error code %ERRORLEVEL%
    pause
    exit /b %ERRORLEVEL%
)

echo Deployment completed successfully!
pause