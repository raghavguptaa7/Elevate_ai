#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logging utilities for Elevate.AI application

This module provides logging utilities for the Elevate.AI application.
"""

import os
import logging
from logging.handlers import RotatingFileHandler

# Ensure logs directory exists
LOGS_DIR = os.path.join(os.getcwd(), 'logs')
os.makedirs(LOGS_DIR, exist_ok=True)

# Configure logger
logger = logging.getLogger('elevate_ai')
logger.setLevel(logging.INFO)

# Create console handler
console_handler = logging.StreamHandler()
console_handler.setLevel(logging.INFO)

# Create file handler for general logs
general_log_file = os.path.join(LOGS_DIR, 'elevate_ai.log')
file_handler = RotatingFileHandler(
    general_log_file, maxBytes=10485760, backupCount=10
)
file_handler.setLevel(logging.INFO)

# Create file handler for error logs
error_log_file = os.path.join(LOGS_DIR, 'error.log')
error_file_handler = RotatingFileHandler(
    error_log_file, maxBytes=10485760, backupCount=10
)
error_file_handler.setLevel(logging.ERROR)

# Create formatter
formatter = logging.Formatter(
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

# Add formatter to handlers
console_handler.setFormatter(formatter)
file_handler.setFormatter(formatter)
error_file_handler.setFormatter(formatter)

# Add handlers to logger
logger.addHandler(console_handler)
logger.addHandler(file_handler)
logger.addHandler(error_file_handler)


def get_logger():
    """Get the application logger."""
    return logger


def log_info(message):
    """Log an info message."""
    logger.info(message)


def log_error(message, exc_info=True):
    """Log an error message."""
    logger.error(message, exc_info=exc_info)


def log_warning(message):
    """Log a warning message."""
    logger.warning(message)


def log_debug(message):
    """Log a debug message."""
    logger.debug(message)


def log_api_request(request, endpoint, status_code=None, response_time=None):
    """
    Log an API request.

    Args:
        request: Flask request object
        endpoint: API endpoint name
        status_code: HTTP status code (optional)
        response_time: Response time in ms (optional)
    """
    client_ip = getattr(request, "remote_addr", "unknown")
    method = getattr(request, "method", "UNKNOWN")

    log_message = f"API Request: {method} {endpoint} from {client_ip}"
    if status_code is not None:
        log_message += f" - Status: {status_code}"
    if response_time is not None:
        log_message += f" - Response Time: {response_time}ms"

    logger.info(log_message)


def log_groq_api_request(prompt_type, tokens_used=None, response_time=None):
    """
    Log a Groq API request.

    Args:
        prompt_type: Type of prompt
        tokens_used: Number of tokens used (optional)
        response_time: Response time in ms (optional)
    """
    log_message = f"Groq API Request: {prompt_type}"
    if tokens_used is not None:
        log_message += f" - Tokens: {tokens_used}"
    if response_time is not None:
        log_message += f" - Response Time: {response_time}ms"

    logger.info(log_message)