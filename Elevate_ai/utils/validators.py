#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Validation utilities for Elevate.AI application

This module provides utilities for validating and sanitizing user input
in the Elevate.AI application.
"""

import re
import html


def sanitize_text(text):
    """
    Sanitize text input to prevent XSS attacks.
    
    Args:
        text: Text to sanitize
        
    Returns:
        str: Sanitized text
    """
    if not text:
        return ""
    
    # Convert to string if not already
    if not isinstance(text, str):
        text = str(text)
    
    # Escape HTML entities
    return html.escape(text)


def validate_email(email):
    """
    Validate email format.
    
    Args:
        email: Email address to validate
        
    Returns:
        bool: True if email is valid, False otherwise
    """
    if not email:
        return False
    
    # Simple email validation regex
    pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
    return bool(re.match(pattern, email))


def validate_length(text, min_length=1, max_length=None):
    """
    Validate text length.
    
    Args:
        text: Text to validate
        min_length: Minimum allowed length
        max_length: Maximum allowed length
        
    Returns:
        bool: True if length is valid, False otherwise
    """
    if not text:
        return min_length == 0
    
    text_length = len(text)
    
    if min_length is not None and text_length < min_length:
        return False
    
    if max_length is not None and text_length > max_length:
        return False
    
    return True


def validate_json_structure(json_data, required_fields):
    """
    Validate JSON structure.
    
    Args:
        json_data: JSON data to validate
        required_fields: List of required field names
        
    Returns:
        tuple: (is_valid, error_message)
    """
    if not json_data:
        return False, "No data provided"
    
    missing_fields = [field for field in required_fields if field not in json_data]
    
    if missing_fields:
        return False, f"Missing required fields: {', '.join(missing_fields)}"
    
    return True, ""


def validate_date_format(date_str, format='%Y-%m-%d'):
    """
    Validate date string format.
    
    Args:
        date_str: Date string to validate
        format: Expected date format
        
    Returns:
        bool: True if date format is valid, False otherwise
    """
    from datetime import datetime
    
    if not date_str:
        return False
    
    try:
        datetime.strptime(date_str, format)
        return True
    except ValueError:
        return False


def validate_numeric(value, min_value=None, max_value=None):
    """
    Validate numeric value.
    
    Args:
        value: Value to validate
        min_value: Minimum allowed value
        max_value: Maximum allowed value
        
    Returns:
        bool: True if value is valid, False otherwise
    """
    try:
        num_value = float(value)
        
        if min_value is not None and num_value < min_value:
            return False
        
        if max_value is not None and num_value > max_value:
            return False
        
        return True
    except (ValueError, TypeError):
        return False


def validate_api_key(api_key):
    """
    Validate API key format.
    
    Args:
        api_key: API key to validate
        
    Returns:
        bool: True if API key format is valid, False otherwise
    """
    if not api_key:
        return False
    
    # Check if API key has a reasonable length and format
    # This is a simple check and should be adjusted based on the actual API key format
    return len(api_key) >= 8 and bool(re.match(r'^[a-zA-Z0-9_\-\.]+$', api_key))