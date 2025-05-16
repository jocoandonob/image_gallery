@echo off
echo Creating CDK virtual environment...
python -m venv cdk-venv
call cdk-venv\Scripts\activate.bat
echo Installing CDK dependencies...
pip install -r requirements-cdk.txt
echo CDK environment setup complete!
echo Run 'cdk-venv\Scripts\activate.bat' to activate the environment