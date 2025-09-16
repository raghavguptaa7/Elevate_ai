#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Database utilities for Elevate.AI application

This module provides utilities for database operations in the Elevate.AI application.
"""

import os
import sqlite3
import json
from contextlib import contextmanager

# Define database path
DATABASE_PATH = os.path.join(os.getcwd(), 'database', 'database.db')

# Ensure database directory exists
os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)


@contextmanager
def get_db_connection():
    """
    Context manager for database connections.
    
    Yields:
        sqlite3.Connection: Database connection object
    """
    conn = sqlite3.connect(DATABASE_PATH)
    conn.row_factory = sqlite3.Row  # This enables column access by name
    try:
        yield conn
    finally:
        conn.close()


def dict_factory(cursor, row):
    """
    Convert database row to dictionary.
    
    Args:
        cursor: Database cursor
        row: Database row
        
    Returns:
        dict: Row as dictionary
    """
    return {col[0]: row[idx] for idx, col in enumerate(cursor.description)}


def query_db(query, args=(), one=False):
    """
    Query the database and return results as dictionaries.
    
    Args:
        query: SQL query string
        args: Query parameters
        one: If True, return only one result
        
    Returns:
        list or dict: Query results
    """
    with get_db_connection() as conn:
        conn.row_factory = dict_factory
        cur = conn.cursor()
        cur.execute(query, args)
        rv = cur.fetchall()
        cur.close()
    return (rv[0] if rv else None) if one else rv


def insert_db(table, data):
    """
    Insert data into a database table.
    
    Args:
        table: Table name
        data: Dictionary of column names and values
        
    Returns:
        int: ID of the inserted row
    """
    columns = ', '.join(data.keys())
    placeholders = ', '.join(['?' for _ in data.keys()])
    query = f"INSERT INTO {table} ({columns}) VALUES ({placeholders})"
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, list(data.values()))
        conn.commit()
        return cur.lastrowid


def update_db(table, data, condition):
    """
    Update data in a database table.
    
    Args:
        table: Table name
        data: Dictionary of column names and values to update
        condition: WHERE condition string
        
    Returns:
        int: Number of rows affected
    """
    set_clause = ', '.join([f"{key} = ?" for key in data.keys()])
    query = f"UPDATE {table} SET {set_clause} WHERE {condition}"
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(query, list(data.values()))
        conn.commit()
        return cur.rowcount


def delete_db(table, condition):
    """
    Delete data from a database table.
    
    Args:
        table: Table name
        condition: WHERE condition string
        
    Returns:
        int: Number of rows affected
    """
    query = f"DELETE FROM {table} WHERE {condition}"
    
    with get_db_connection() as conn:
        cur = conn.cursor()
        cur.execute(query)
        conn.commit()
        return cur.rowcount


def store_json_data(table, data, json_columns):
    """
    Store data with JSON columns in a database table.
    
    Args:
        table: Table name
        data: Dictionary of column names and values
        json_columns: List of column names that contain JSON data
        
    Returns:
        int: ID of the inserted row
    """
    # Convert JSON columns to strings
    for col in json_columns:
        if col in data and data[col] is not None:
            data[col] = json.dumps(data[col])
    
    return insert_db(table, data)


def get_json_data(table, condition, json_columns):
    """
    Get data with JSON columns from a database table.
    
    Args:
        table: Table name
        condition: WHERE condition string
        json_columns: List of column names that contain JSON data
        
    Returns:
        list: Query results with JSON columns parsed
    """
    query = f"SELECT * FROM {table} WHERE {condition}"
    results = query_db(query)
    
    # Parse JSON columns
    for row in results:
        for col in json_columns:
            if col in row and row[col] is not None:
                try:
                    row[col] = json.loads(row[col])
                except (json.JSONDecodeError, TypeError):
                    pass
    
    return results