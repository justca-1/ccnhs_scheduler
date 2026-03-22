"""
src/database.py - Handles the SQLite database creation and pathing.
"""

import sqlite3
import logging
from pathlib import Path

def get_db_path():
    """Returns the persistent path for the database in the user's Documents folder."""
    # Create a subfolder so we don't clutter their main Documents folder
    app_dir = Path.home() / "Documents" / "CCNHS_Scheduler"
    app_dir.mkdir(parents=True, exist_ok=True) 
    return str(app_dir / "school_scheduler.db")

def init_db(db_path=None):
    """Initializes the database schema using the centralized path logic."""
    if db_path is None:
        db_path = get_db_path()
        
    logging.info(f"DATABASE IS AT: {db_path}")

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
                          room TEXT,
                          FOREIGN KEY(person_id) REFERENCES Person(person_id))''')
        
        # Migration: Add 'subject' column if it doesn't exist (for existing DBs)
        try:
            cursor.execute("ALTER TABLE Schedule ADD COLUMN subject TEXT")
        except sqlite3.OperationalError:
            pass # Column likely already exists
            
        # Migration: Add 'room' column if it doesn't exist
        try:
            cursor.execute("ALTER TABLE Schedule ADD COLUMN room TEXT")
        except sqlite3.OperationalError:
            pass # Column likely already exists
            
        conn.commit()
    return db_path