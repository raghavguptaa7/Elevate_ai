#!/bin/bash

# Setup script for Elevate.AI application

echo "Setting up Elevate.AI application..."

# Create virtual environment
echo "Creating virtual environment..."
python -m venv venv

# Activate virtual environment
echo "Activating virtual environment..."
source venv/bin/activate

# Install requirements
echo "Installing requirements..."
pip install -r requirements.txt

# Create .env file from example if it doesn't exist
if [ ! -f .env ]; then
    echo "Creating .env file from example..."
    cp .env.example .env
    echo "Please edit .env file and add your Groq API key"
fi

# Initialize database
echo "Initializing database..."
python init_db.py

echo "Setup complete! You can now run the application with 'python run.py'"