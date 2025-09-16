#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Error handling utilities for Elevate.AI application

This module provides standardized error handling for the Elevate.AI application.
"""

from flask import jsonify, render_template


def register_error_handlers(app):
    """
    Register error handlers for the Flask application.
    
    Args:
        app: Flask application instance
    """
    
    @app.errorhandler(400)
    def bad_request(error):
        """
        Handle 400 Bad Request errors.
        """
        if request_wants_json():
            return jsonify({
                'error': 'Bad Request',
                'message': str(error)
            }), 400
        return render_template('error.html', error_code=400, error_message='Bad Request'), 400
    
    @app.errorhandler(404)
    def not_found(error):
        """
        Handle 404 Not Found errors.
        """
        if request_wants_json():
            return jsonify({
                'error': 'Not Found',
                'message': 'The requested resource was not found.'
            }), 404
        return render_template('error.html', error_code=404, error_message='Page Not Found'), 404
    
    @app.errorhandler(500)
    def internal_server_error(error):
        """
        Handle 500 Internal Server Error errors.
        """
        if request_wants_json():
            return jsonify({
                'error': 'Internal Server Error',
                'message': 'An unexpected error occurred.'
            }), 500
        return render_template('error.html', error_code=500, error_message='Internal Server Error'), 500


def request_wants_json():
    """
    Determine if the request wants a JSON response.
    
    Returns:
        bool: True if the request wants JSON, False otherwise
    """
    from flask import request
    best = request.accept_mimetypes.best_match(['application/json', 'text/html'])
    return best == 'application/json' and \
        request.accept_mimetypes[best] > request.accept_mimetypes['text/html']


def api_error(message, status_code=400):
    """
    Create a standardized API error response.
    
    Args:
        message: Error message
        status_code: HTTP status code
        
    Returns:
        tuple: JSON response and status code
    """
    return jsonify({
        'error': True,
        'message': message
    }), status_code