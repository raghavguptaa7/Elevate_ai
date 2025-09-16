#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Run script for Elevate.AI application

This script provides a convenient way to run the Elevate.AI Flask application.
It loads environment variables from .env file and starts the Flask server.
"""

import os
from dotenv import load_dotenv
from app import app
from utils.config import get_config
from utils.logger import log_info

# Load environment variables from .env file
load_dotenv()

# Get configuration
config = get_config()

if __name__ == '__main__':
    log_info(f"Starting {config.APP_NAME} v{config.APP_VERSION}")
    
    # Run the Flask application
    app.run(host=config.HOST, port=config.PORT, debug=config.DEBUG)