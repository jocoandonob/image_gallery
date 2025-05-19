@echo off
echo Deploying Winston Gallery infrastructure stacks...

cd %~dp0
python app.py

echo Deployment complete!
pause