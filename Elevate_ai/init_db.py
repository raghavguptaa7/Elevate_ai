#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database initialization script for Elevate.AI

This script initializes the SQLite database with the necessary tables
for the Elevate.AI application. It creates tables for resumes, interviews,
syllabi, quizzes, study plans, and progress tracking.

Usage:
    python init_db.py
"""

import os
import sqlite3
from datetime import datetime
from utils.db_utils import get_db_connection
from utils.config import get_config
from utils.logger import get_logger, log_info, log_error

# Initialize logger
logger = get_logger()

# Get configuration
config = get_config()

# Database file path
DB_PATH = os.path.join(os.getcwd(), config.DATABASE_PATH)

# SQL statements to create tables
CREATE_TABLES = [
    """
    CREATE TABLE IF NOT EXISTS resumes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        filename TEXT NOT NULL,
        content TEXT NOT NULL,
        job_description TEXT NOT NULL,
        analysis TEXT,
        match_score REAL,
        strengths TEXT,
        gaps TEXT,
        suggestions TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS interviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        job_role TEXT NOT NULL,
        questions TEXT NOT NULL,
        answers TEXT,
        feedback TEXT,
        overall_score REAL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS syllabi (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        subject TEXT NOT NULL,
        content TEXT NOT NULL,
        parsed_topics TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS quizzes (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        syllabus_id INTEGER NOT NULL,
        topics TEXT NOT NULL,
        questions TEXT NOT NULL,
        answers TEXT,
        score REAL,
        feedback TEXT,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (syllabus_id) REFERENCES syllabi (id)
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS study_plans (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        syllabus_id INTEGER NOT NULL,
        duration_days INTEGER NOT NULL,
        hours_per_day REAL NOT NULL,
        plan_data TEXT NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (syllabus_id) REFERENCES syllabi (id)
    )
    """,
    
    """
    CREATE TABLE IF NOT EXISTS progress (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id TEXT NOT NULL,
        syllabus_id INTEGER NOT NULL,
        topic TEXT NOT NULL,
        mastery_level REAL NOT NULL,
        quiz_count INTEGER DEFAULT 0,
        study_hours REAL DEFAULT 0,
        last_quiz_id INTEGER,
        updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (syllabus_id) REFERENCES syllabi (id),
        FOREIGN KEY (last_quiz_id) REFERENCES quizzes (id)
    )
    """
]

def init_db():
    """Initialize the database with required tables"""
    log_info(f"Initializing database at {DB_PATH}...")
    
    # Create database directory if it doesn't exist
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    
    try:
        # Connect to database using context manager
        with get_db_connection() as conn:
            cursor = conn.cursor()
            
            # Create tables
            for create_table_sql in CREATE_TABLES:
                cursor.execute(create_table_sql)
            
            # Commit changes
            conn.commit()
        
        log_info("Database initialization complete!")
    except Exception as e:
        log_error(f"Error initializing database: {str(e)}")
        raise

def add_sample_data():
    """Add sample data to the database for testing"""
    log_info("Adding sample data...")
    
    try:
        # Connect to database using context manager
        with get_db_connection() as conn:
            cursor = conn.cursor()
        
            # Sample user ID
            user_id = "sample_user"
            
            # Sample syllabus
            cursor.execute(
                "INSERT INTO syllabi (user_id, subject, content, parsed_topics) VALUES (?, ?, ?, ?)",
                (
                    user_id,
                    "Introduction to Computer Science",
                    "This course covers the basics of computer science, including algorithms, data structures, and programming concepts.",
                    "[\"Algorithms\", \"Data Structures\", \"Programming Concepts\", \"Computational Complexity\", \"Object-Oriented Programming\"]"
                )
            )
            syllabus_id = cursor.lastrowid
            
            # Sample quiz
            cursor.execute(
                "INSERT INTO quizzes (user_id, syllabus_id, topics, questions, answers, score, feedback) VALUES (?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    syllabus_id,
                    "[\"Algorithms\", \"Data Structures\"]",
                    "[{\"question\": \"What is the time complexity of binary search?\", \"options\": [\"O(1)\", \"O(log n)\", \"O(n)\", \"O(n log n)\"], \"correct\": 1}]",
                    "[1]",
                    100.0,
                    "Great job! You have a good understanding of algorithm complexity."
                )
            )
            quiz_id = cursor.lastrowid
            
            # Sample progress
            for topic in ["Algorithms", "Data Structures", "Programming Concepts", "Computational Complexity", "Object-Oriented Programming"]:
                mastery = 85.0 if topic in ["Algorithms", "Data Structures"] else 50.0
                cursor.execute(
                    "INSERT INTO progress (user_id, syllabus_id, topic, mastery_level, quiz_count, study_hours, last_quiz_id) VALUES (?, ?, ?, ?, ?, ?, ?)",
                    (
                        user_id,
                        syllabus_id,
                        topic,
                        mastery,
                        1 if topic in ["Algorithms", "Data Structures"] else 0,
                        2.5 if topic in ["Algorithms", "Data Structures"] else 1.0,
                        quiz_id if topic in ["Algorithms", "Data Structures"] else None
                    )
                )
            
            # Sample study plan
            plan_data = {
                "plan": [
            {
                "day": 1,
                "date": datetime.now().strftime("%Y-%m-%d"),
                "topics": ["Algorithms", "Data Structures"],
                "duration_hours": 2,
                "activities": ["Review binary search algorithm", "Practice implementing linked lists"],
                "resources": ["Introduction to Algorithms textbook", "Online coding platform"]
            }
        ]
    }
    
            cursor.execute(
                "INSERT INTO study_plans (user_id, syllabus_id, duration_days, hours_per_day, plan_data) VALUES (?, ?, ?, ?, ?)",
                (
                    user_id,
                    syllabus_id,
                    30,
                    2.0,
                    str(plan_data)
                )
            )
            
            # Sample resume
            cursor.execute(
                "INSERT INTO resumes (user_id, filename, content, job_description, analysis, match_score, strengths, gaps, suggestions) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    "sample_resume.pdf",
                    "John Doe\nSoftware Engineer\n5 years of experience in Python and JavaScript development.",
                    "Looking for a Software Engineer with Python experience and knowledge of web frameworks.",
                    "The resume shows good experience with Python which matches the job requirements.",
                    85.0,
                    "[\"Python experience\", \"Software engineering background\"]",
                    "[\"No specific mention of web frameworks\", \"Limited detail on projects\"]",
                    "[\"Add details about experience with web frameworks\", \"Include specific projects and outcomes\"]"
                )
            )
            
            # Sample interview
            cursor.execute(
                "INSERT INTO interviews (user_id, job_role, questions, answers, feedback, overall_score) VALUES (?, ?, ?, ?, ?, ?)",
                (
                    user_id,
                    "Software Engineer",
                    "[\"Describe your experience with Python\", \"How do you handle code reviews?\"]",
                    "[\"I have 5 years of experience with Python, primarily building web applications and data processing systems.\", \"I approach code reviews constructively, focusing on both code quality and knowledge sharing.\"]",
                    "[{\"question_idx\": 0, \"score\": 90, \"feedback\": \"Good detailed answer showing relevant experience\"}, {\"question_idx\": 1, \"score\": 85, \"feedback\": \"Good approach to code reviews, could add more specific examples\"}]",
                    87.5
                )
            )
            
            # Commit changes
            conn.commit()
        
        log_info("Sample data added successfully!")
    except Exception as e:
        log_error(f"Error adding sample data: {str(e)}")
        raise

if __name__ == "__main__":
    try:
        log_info(f"Starting database initialization for {config.APP_NAME}")
        init_db()
        
        # Ask if user wants to add sample data
        add_samples = input("Do you want to add sample data for testing? (y/n): ").lower().strip()
        if add_samples == 'y' or add_samples == 'yes':
            add_sample_data()
        
        log_info("Database setup complete!")
        print("Database setup complete!")
    except Exception as e:
        log_error(f"Database setup failed: {str(e)}")
        print(f"Database setup failed: {str(e)}")
        exit(1)