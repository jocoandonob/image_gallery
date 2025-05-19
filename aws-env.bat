@echo off
echo Setting up AWS environment variables...

REM Get S3 bucket name from CDK output
FOR /F "tokens=* USEBACKQ" %%F IN (`aws cloudformation describe-stacks --stack-name WinstonGalleryVpcS3Stack --query "Stacks[0].Outputs[?OutputKey=='BucketName'].OutputValue" --output text`) DO (
  SET S3_BUCKET=%%F
)

REM Get DB secret ARN from CDK output
FOR /F "tokens=* USEBACKQ" %%F IN (`aws cloudformation describe-stacks --stack-name WinstonGalleryRdsStack --query "Stacks[0].Outputs[?OutputKey=='DBSecretArn'].OutputValue" --output text`) DO (
  SET DB_SECRET_ARN=%%F
)

REM Get DB endpoint from CDK output
FOR /F "tokens=* USEBACKQ" %%F IN (`aws cloudformation describe-stacks --stack-name WinstonGalleryRdsStack --query "Stacks[0].Outputs[?OutputKey=='DBEndpoint'].OutputValue" --output text`) DO (
  SET DB_ENDPOINT=%%F
)

REM Get DB password from Secrets Manager
FOR /F "tokens=* USEBACKQ" %%F IN (`aws secretsmanager get-secret-value --secret-id %DB_SECRET_ARN% --query "SecretString" --output text`) DO (
  SET DB_SECRET=%%F
)

REM Extract password from JSON (this is a simplified approach)
echo %DB_SECRET% > temp.json
FOR /F "tokens=* USEBACKQ" %%F IN (`type temp.json ^| findstr /C:"password"`) DO (
  SET PASSWORD_LINE=%%F
)
SET DB_PASSWORD=%PASSWORD_LINE:*password":"=%
SET DB_PASSWORD=%DB_PASSWORD:","=%
DEL temp.json

echo S3_BUCKET=%S3_BUCKET%
echo DB_ENDPOINT=%DB_ENDPOINT%
echo DB_SECRET_ARN=%DB_SECRET_ARN%

echo Setting environment variables...
setx S3_BUCKET %S3_BUCKET%
setx DB_ENDPOINT %DB_ENDPOINT%
setx DB_SECRET_ARN %DB_SECRET_ARN%
setx DB_PASSWORD %DB_PASSWORD%

echo Environment variables set successfully!
pause