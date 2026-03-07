import sqlite3
from typing import List, Dict
from datetime import datetime, timedelta

class ScheduleEngine:
    """
    The central logic engine for the scheduling system.
    Handles all SQLite interactions and conflict detection math.
    """

    def __init__(self, db_path: str):
        """Initializes the engine with the path to the local SQLite file."""
        self.db_path = db_path

    # --- PERSON MANAGEMENT ---

    def add_person(self, name: str, role: str = "") -> bool:
        """Adds a new person to the database."""
        if not name:
            return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO Person (full_name, role) VALUES (?, ?)", 
                    (name, role)
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database Error (add_person): {e}")
            return False

    def update_person_name(self, person_id: int, new_name: str) -> bool:
        """Updates the full name of a person."""
        if not new_name:
            return False
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "UPDATE Person SET full_name = ? WHERE person_id = ?", 
                    (new_name, person_id)
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Update Error: {e}")
            return False

    def get_all_persons(self) -> List[Dict]:
        """Fetches all registered persons as a list of dictionaries."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT person_id, full_name, role FROM Person")
                return [dict(row) for row in cursor.fetchall()]
        except sqlite3.Error:
            return []

    # --- SCHEDULE MANAGEMENT ---

    def can_assign(self, person_id: int, day: str, start: str, end: str) -> bool:
        """
        Checks if a person is free during the requested time slot.
        Returns True if assignment is possible (no overlap), False otherwise.
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # Overlap logic: (StartA < EndB) and (EndA > StartB)
                query = "SELECT COUNT(*) FROM Schedule WHERE person_id = ? AND day = ? AND start_time < ? AND end_time > ?"
                cursor.execute(query, (person_id, day, end, start))
                return cursor.fetchone()[0] == 0
        except sqlite3.Error as e:
            print(f"Conflict Check Error: {e}")
            return False

    def add_schedule(self, person_id: int, day: str, start: str, end: str, grade_level: str, subject: str = "") -> bool:
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute(
                    "INSERT INTO Schedule (person_id, day, start_time, end_time, grade_level, subject) VALUES (?, ?, ?, ?, ?, ?)",
                    (person_id, day, start, end, grade_level, subject)
                )
                conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Database Error: {e}")
            return False

    def get_weekly_schedule_map(self, person_id=None) -> dict:
        """
        Maps (Day, Time) to a list of info DICTIONARIES.
        Returns: {(Day, TimeStr): [{'name': '...', ...}, ...]}
        Refactored to use datetime objects and interval overlap logic.
        If person_id is provided, filters for that specific person.
        """
        schedule_map = {}
        
        query = """
        SELECT p.full_name, p.role, s.day, s.start_time, s.end_time, s.grade_level, s.subject 
        FROM Schedule s
        JOIN Person p ON s.person_id = p.person_id
        """
        
        params = ()
        if person_id:
            query += " WHERE s.person_id = ?"
            params = (person_id,)
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute(query, params)
                rows = cursor.fetchall()

            # 1. Define UI Grid Slots (Intervals)
            # We generate 30-min slots from 06:00 to 19:00
            ui_slots = []
            current_dt = datetime.strptime("06:00", "%H:%M")
            end_dt = datetime.strptime("19:00", "%H:%M")
            
            while current_dt < end_dt:
                slot_start = current_dt.time()
                next_dt = current_dt + timedelta(minutes=30)
                slot_end = next_dt.time()
                
                # Key used by UI (e.g., "06:00")
                key_str = slot_start.strftime("%H:%M")
                ui_slots.append({
                    "key": key_str,
                    "start": slot_start,
                    "end": slot_end
                })
                current_dt = next_dt

            for row in rows:
                # Normalize Time: Convert DB strings to datetime.time
                try:
                    sched_start = datetime.strptime(row['start_time'], "%H:%M").time()
                    sched_end = datetime.strptime(row['end_time'], "%H:%M").time()
                except (ValueError, TypeError):
                    continue # Skip invalid time formats

                # PACKAGE AS A DICTIONARY (This fixes your crash!)
                info = {
                    "name": row['full_name'],
                    "role": row['role'] if row['role'] else "No Role",
                    "subject": row['subject'] if row['subject'] else "",
                    "range": f"{row['start_time']} - {row['end_time']}",
                    "grade_level": row['grade_level']
                }
                
                day = row['day']

                # Interval Comparison: Check overlap with every UI slot
                # Overlap Rule: (StartA < EndB) and (StartB < EndA)
                for slot in ui_slots:
                    if slot['start'] < sched_end and sched_start < slot['end']:
                        key = (day, slot['key'])
                        if key not in schedule_map:
                            schedule_map[key] = []
                        # Store the dictionary, not just the name string
                        schedule_map[key].append(info)
            
            return schedule_map
        except sqlite3.Error as e:
            print(f"Database error in get_weekly_schedule_map: {e}")
            return {}

    def validate_workload(self, person_id: int) -> dict:
        """
        Calculates load per day to enforce the 6-hour (360 min) teaching limit.
        Returns: {'daily': {day: mins}, 'total': int, 'overloaded': [days], 'details': {day: [slots]}}
        """
        stats = {"daily": {}, "total": 0, "overloaded": [], "details": {}}
        
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                cursor.execute("SELECT day, start_time, end_time FROM Schedule WHERE person_id = ?", (person_id,))
                rows = cursor.fetchall()

            for row in rows:
                day = row['day']
                fmt = "%H:%M"
                # Parse times
                t1 = datetime.strptime(row['start_time'], fmt)
                t2 = datetime.strptime(row['end_time'], fmt)
                
                # Calculate duration in minutes
                duration = (t2 - t1).total_seconds() / 60
                
                stats["daily"][day] = stats["daily"].get(day, 0) + duration
                stats["total"] += duration
                
                if day not in stats["details"]:
                    stats["details"][day] = []
                stats["details"][day].append(f"{row['start_time']} - {row['end_time']}")

            # Flag days exceeding 6 hours (360 minutes)
            stats["overloaded"] = [d for d, m in stats["daily"].items() if m > 360]
            return stats
        except sqlite3.Error as e:
            print(f"Workload Calc Error: {e}")
            return stats

    def clear_all_data(self) -> bool:
        """Wipes the database - Use with caution!"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Schedule")
                cursor.execute("DELETE FROM Person")
                conn.commit()
            return True
        except sqlite3.Error:
            return False
    
    def delete_person(self, person_id: int) -> bool:
        """Removes a person and all their associated schedules."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                # 1. Remove their schedules first (to maintain integrity)
                cursor.execute("DELETE FROM Schedule WHERE person_id = ?", (person_id,))
                # 2. Remove the person
                cursor.execute("DELETE FROM Person WHERE person_id = ?", (person_id,))
                conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Delete Error: {e}")
            return False
        

    def clear_only_schedules(self) -> bool:
        """Deletes all rows from the Schedule table but keeps the Person table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("DELETE FROM Schedule")
                conn.commit()
            return True
        except sqlite3.Error:
            return False

    def get_total_schedule_count(self) -> int:
        """Returns the total number of busy blocks (rows) in the Schedule table."""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                cursor.execute("SELECT COUNT(*) FROM Schedule")
                return cursor.fetchone()[0]
        except sqlite3.Error:
            return 0
            
    def get_person_backup(self, person_id: int) -> dict:
        """Retrieves person details and their schedules for backup before delete."""
        data = {}
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                
                # Get Person
                cursor.execute("SELECT * FROM Person WHERE person_id = ?", (person_id,))
                p_row = cursor.fetchone()
                if not p_row: return None
                data['person'] = dict(p_row)
                
                # Get Schedules
                cursor.execute("SELECT * FROM Schedule WHERE person_id = ?", (person_id,))
                data['schedules'] = [dict(row) for row in cursor.fetchall()]
                
        except sqlite3.Error as e:
            print(f"Backup Error: {e}")
            return None
        return data

    def restore_person_data(self, backup_data: dict) -> bool:
        """Restores a person and their schedules from backup."""
        try:
            p = backup_data['person']
            schedules = backup_data['schedules']
            
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                # Restore Person (Force ID to maintain consistency)
                cursor.execute(
                    "INSERT INTO Person (person_id, full_name, role) VALUES (?, ?, ?)",
                    (p['person_id'], p['full_name'], p['role'])
                )
                
                # Restore Schedules
                for s in schedules:
                    cursor.execute(
                        "INSERT INTO Schedule (person_id, day, start_time, end_time, grade_level, subject) VALUES (?, ?, ?, ?, ?, ?)",
                        (p['person_id'], s['day'], s['start_time'], s['end_time'], s['grade_level'], s['subject'])
                    )
                conn.commit()
            return True
        except sqlite3.Error as e:
            print(f"Restore Error: {e}")
            return False

class DepEdValidator(ScheduleEngine):
    """
    Encapsulates specific Department of Education (DepEd) rules.
    Inherits from ScheduleEngine to separate Data Logic from Business Rules.
    """

    def calculate_weighted_load(self, person_id: int) -> float:
        """
        Calculates load points using subject weights and precise time math.
        """
        # Dictionary Mapping: Subject weights
        weights = {
            "Math": 50,
            "Science": 50,
            "English": 40,
            "Filipino": 40
        }

        total_points = 0.0

        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.row_factory = sqlite3.Row
                cursor = conn.cursor()
                # UPDATED: Use 'subject' from Schedule instead of 'role' from Person
                query = """
                SELECT subject, start_time, end_time 
                FROM Schedule
                WHERE person_id = ?
                """
                cursor.execute(query, (person_id,))
                rows = cursor.fetchall()

            for row in rows:
                # Normalize Time
                fmt = "%H:%M"
                t1 = datetime.strptime(row['start_time'], fmt)
                t2 = datetime.strptime(row['end_time'], fmt)

                # The Breakdown: Reliable time math
                duration_minutes = (t2 - t1).total_seconds() / 60
                duration_hours = duration_minutes / 60

                # The Breakdown: Dictionary Mapping with fallback
                subject_name = row['subject'] if row['subject'] else ""
                weight = weights.get(subject_name, 40)

                total_points += duration_hours * weight

            return total_points

        except sqlite3.Error as e:
            print(f"DepEd Validation Error: {e}")
            return 0.0