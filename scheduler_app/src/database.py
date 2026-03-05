"""
src/database.py - Handles the SQLite database creation and pathing.
"""

import sqlite3
import os

def get_db_path() -> str:
    """
    Returns the absolute path to the database file.
    Creates a folder in the user's home directory to ensure it's writable.
    """
    # Using 'expanduser' ensures this works on both Windows and Mac
    base_dir = os.path.join(os.path.expanduser("~"), "SchedulerApp")
    
    if not os.path.exists(base_dir):
        os.makedirs(base_dir)
        
    return os.path.join(base_dir, "schedule_v1.db")

def init_db() -> str:
    """
    Connects to SQLite (creating the file if it doesn't exist)
    and sets up the tables.
    """
    # This ensures we know exactly where the file is
    db_path = os.path.join(os.getcwd(), "school_scheduler.db")
    print(f"!!! DATABASE IS AT: {db_path}") 

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Person 
                         (person_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          full_name TEXT, role TEXT)''')
        
        # Check carefully that 'grade_level TEXT' is inside the parentheses
        cursor.execute('''CREATE TABLE IF NOT EXISTS Schedule 
                         (schedule_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          person_id INTEGER, 
                          day TEXT, 
                          start_time TEXT, 
                          end_time TEXT, 
                          grade_level TEXT, 
                          subject TEXT,
                          FOREIGN KEY(person_id) REFERENCES Person(person_id))''')
        
        # Migration: Add 'subject' column if it doesn't exist (for existing DBs)
        try:
            cursor.execute("ALTER TABLE Schedule ADD COLUMN subject TEXT")
        except sqlite3.OperationalError:
            pass # Column likely already exists
            
        conn.commit()
    return db_path