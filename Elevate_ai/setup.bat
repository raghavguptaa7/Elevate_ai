@echo off
REM Setup script for Elevate.AI application on Windows

echo Setting up Elevate.AI application...

REM Create virtual environment
echo Creating virtual environment...
python -m venv venv

REM Activate virtual environment
echo Activating virtual environment...
call venv\Scripts\activate.bat

REM Install requirements
echo Installing requirements...
pip install -r requirements.txt

REM Create .env file from example if it doesn't exist
if not exist .env (
    echo Creating .env file from example...
    copy .env.example .env
    echo Please edit .env file and add your Groq API key
)

REM Initialize database
echo Initializing database...
python init_db.py

echo Setup complete! You can now run the application with 'python run.py'
pause