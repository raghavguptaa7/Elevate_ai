#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Configuration utilities for Elevate.AI application

This module provides configuration utilities for the Elevate.AI application.
"""

import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()


class Config:
    """
    Configuration class for Elevate.AI application.
    """
    
    # Flask configuration
    SECRET_KEY = os.getenv('SECRET_KEY', os.urandom(24).hex())
    DEBUG = os.getenv('FLASK_DEBUG', 'True').lower() == 'true'
    
    # Database configuration
    DATABASE_PATH = os.getenv('DATABASE_PATH', 'database/database.db')
    
    # Groq API configuration
    GROQ_API_KEY = os.getenv('GROQ_API_KEY')
    GROQ_API_BASE_URL = os.getenv('GROQ_API_BASE_URL', 'https://api.groq.com/openai/v1/chat/completions')
    GROQ_API_MODEL = os.getenv('GROQ_API_MODEL', 'llama2-70b-4096')
    
    # File upload configuration
    UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')
    MAX_CONTENT_LENGTH = 16 * 1024 * 1024  # 16 MB
    
    # Logging configuration
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    # Server configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    
    # Application configuration
    APP_NAME = 'Elevate.AI'
    APP_VERSION = '1.0.0'
    
    # Career module configuration
    RESUME_ANALYSIS_MAX_LENGTH = 10000
    INTERVIEW_MAX_QUESTIONS = 10
    
    # Study module configuration
    SYLLABUS_MAX_LENGTH = 20000
    QUIZ_MAX_QUESTIONS = 20
    STUDY_PLAN_MAX_DAYS = 90


def get_config():
    """
    Get application configuration.
    
    Returns:
        Config: Application configuration
    """
    return Config


def validate_config():
    """
    Validate application configuration.
    
    Returns:
        tuple: (is_valid, error_message)
    """
    config = get_config()
    
    # Check required configuration
    if not config.GROQ_API_KEY:
        return False, "GROQ_API_KEY is not set. Please set it in the .env file."
    
    # Check database directory
    db_dir = os.path.dirname(os.path.join(os.getcwd(), config.DATABASE_PATH))
    if not os.path.exists(db_dir):
        try:
            os.makedirs(db_dir, exist_ok=True)
        except Exception as e:
            return False, f"Failed to create database directory: {str(e)}"
    
    # Check upload directory
    if not os.path.exists(config.UPLOAD_FOLDER):
        try:
            os.makedirs(config.UPLOAD_FOLDER, exist_ok=True)
        except Exception as e:
            return False, f"Failed to create upload directory: {str(e)}"
    
    return True, ""