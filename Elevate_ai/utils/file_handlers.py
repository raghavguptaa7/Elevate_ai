#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
File handling utilities for Elevate.AI application

This module provides utilities for handling file uploads and processing
in the Elevate.AI application.
"""

import os
import uuid
from werkzeug.utils import secure_filename
import PyPDF2

# Define allowed file extensions
ALLOWED_EXTENSIONS = {
    'resume': {'pdf', 'docx', 'txt'},
    'syllabus': {'pdf', 'docx', 'txt'}
}

# Define upload folder
UPLOAD_FOLDER = os.path.join(os.getcwd(), 'uploads')

# Ensure upload folder exists
os.makedirs(UPLOAD_FOLDER, exist_ok=True)


def allowed_file(filename, file_type):
    """
    Check if a file has an allowed extension for the given file type.
    
    Args:
        filename: Name of the file to check
        file_type: Type of file ('resume' or 'syllabus')
        
    Returns:
        bool: True if file extension is allowed, False otherwise
    """
    return '.' in filename and \
           filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS.get(file_type, set())


def save_uploaded_file(file, file_type):
    """
    Save an uploaded file to the upload folder with a secure filename.
    
    Args:
        file: File object from request.files
        file_type: Type of file ('resume' or 'syllabus')
        
    Returns:
        tuple: (success, filepath or error message)
    """
    if file and file.filename:
        if allowed_file(file.filename, file_type):
            # Create a secure filename with a UUID to avoid collisions
            filename = secure_filename(file.filename)
            unique_filename = f"{uuid.uuid4()}_{filename}"
            
            # Create type-specific subfolder
            subfolder = os.path.join(UPLOAD_FOLDER, file_type)
            os.makedirs(subfolder, exist_ok=True)
            
            # Save the file
            filepath = os.path.join(subfolder, unique_filename)
            file.save(filepath)
            
            return True, filepath
        else:
            return False, f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS.get(file_type, []))}"
    return False, "No file provided"


def extract_text_from_pdf(filepath):
    """
    Extract text content from a PDF file.
    
    Args:
        filepath: Path to the PDF file
        
    Returns:
        str: Extracted text content
    """
    text = ""
    try:
        with open(filepath, 'rb') as file:
            reader = PyPDF2.PdfReader(file)
            for page in reader.pages:
                text += page.extract_text() + "\n"
    except Exception as e:
        text = f"Error extracting text: {str(e)}"
    
    return text


def extract_text_from_file(filepath):
    """
    Extract text content from a file based on its extension.
    
    Args:
        filepath: Path to the file
        
    Returns:
        str: Extracted text content
    """
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    if ext == '.pdf':
        return extract_text_from_pdf(filepath)
    elif ext == '.txt':
        try:
            with open(filepath, 'r', encoding='utf-8') as file:
                return file.read()
        except Exception as e:
            return f"Error reading text file: {str(e)}"
    elif ext == '.docx':
        try:
            # This requires python-docx package
            import docx
            doc = docx.Document(filepath)
            return '\n'.join([para.text for para in doc.paragraphs])
        except ImportError:
            return "Error: python-docx package not installed. Cannot extract text from DOCX files."
        except Exception as e:
            return f"Error extracting text from DOCX: {str(e)}"
    else:
        return f"Unsupported file format: {ext}"


def cleanup_old_files(max_age_days=7):
    """
    Clean up files older than the specified age.
    
    Args:
        max_age_days: Maximum age of files in days
        
    Returns:
        int: Number of files deleted
    """
    import time
    from datetime import datetime, timedelta
    
    now = time.time()
    cutoff = now - (max_age_days * 86400)
    count = 0
    
    for root, dirs, files in os.walk(UPLOAD_FOLDER):
        for file in files:
            filepath = os.path.join(root, file)
            if os.path.isfile(filepath):
                if os.path.getmtime(filepath) < cutoff:
                    os.remove(filepath)
                    count += 1
    
    return count