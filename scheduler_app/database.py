"""
src/core/database.py - Handles the SQLite database creation and pathing.
"""

import sqlite3
import os

def get_db_path() -> str:
    """
    Returns the absolute path to the database file in the 'data' folder.
    """
    # We assume main.py is run from the root folder
    base_dir = os.getcwd()
    data_dir = os.path.join(base_dir, "data")
    
    if not os.path.exists(data_dir):
        os.makedirs(data_dir)
        
    return os.path.join(data_dir, "scheduler.db")

def init_db() -> str:
    """
    Connects to SQLite (creating the file if it doesn't exist)
    and sets up the tables.
    """
    db_path = get_db_path()
    print(f"!!! DATABASE IS AT: {db_path}") 

    with sqlite3.connect(db_path) as conn:
        cursor = conn.cursor()
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Person 
                         (person_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          full_name TEXT, role TEXT)''')
        
        cursor.execute('''CREATE TABLE IF NOT EXISTS Schedule 
                         (schedule_id INTEGER PRIMARY KEY AUTOINCREMENT, 
                          person_id INTEGER, 
                          day TEXT, 
                          start_time TEXT, 
                          end_time TEXT, 
                          grade_level TEXT, 
                          subject TEXT,
                          FOREIGN KEY(person_id) REFERENCES Person(person_id))''')
        
        conn.commit()
    return db_path