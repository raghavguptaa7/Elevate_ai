#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Basic tests for Elevate.AI application

This module contains basic tests to verify the functionality of the Elevate.AI Flask application.
"""

import os
import sys
import unittest

# Add parent directory to path to import app
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app import app


class TestApp(unittest.TestCase):
    """Test case for the Flask application"""

    def setUp(self):
        """Set up test client"""
        self.app = app.test_client()
        self.app.testing = True

    def test_home_page(self):
        """Test that home page loads"""
        response = self.app.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Elevate.AI', response.data)

    def test_career_routes_exist(self):
        """Test that career routes are registered"""
        response = self.app.get('/career/resume')
        self.assertEqual(response.status_code, 200)
        
        response = self.app.get('/career/interview')
        self.assertEqual(response.status_code, 200)

    def test_study_routes_exist(self):
        """Test that study routes are registered"""
        response = self.app.get('/study/syllabus')
        self.assertEqual(response.status_code, 200)
        
        response = self.app.get('/study/quiz')
        self.assertEqual(response.status_code, 200)
        
        response = self.app.get('/study/plan')
        self.assertEqual(response.status_code, 200)
        
        response = self.app.get('/study/progress')
        self.assertEqual(response.status_code, 200)


if __name__ == '__main__':
    unittest.main()