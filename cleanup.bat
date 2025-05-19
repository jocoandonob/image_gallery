@echo off
echo Cleaning up old ImageGallery files...

echo Removing app_infrastructure.py
if exist app_infrastructure.py del app_infrastructure.py

echo Removing old batch files
if exist deploy-cdk.bat del deploy-cdk.bat
if exist bootstrap-cdk.bat del bootstrap-cdk.bat
if exist deploy-with-bootstrap.bat del deploy-with-bootstrap.bat
if exist build-and-push.bat del build-and-push.bat

echo Cleanup complete!
echo.
echo Winston Gallery files are ready to use:
echo - winston_vpc_s3_stack.py
echo - winston_ecr_stack.py
echo - winston_rds_stack.py
echo - winston_ecs_alb_stack.py
echo - winston_infrastructure.py
echo - winston_build_push.bat
echo - winston_deploy.md
echo.
echo See winston_deploy.md for deployment instructions.
pause