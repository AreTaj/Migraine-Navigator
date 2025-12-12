
import os
import re
import sqlite3
import pandas as pd
from datetime import datetime

class EntryService:
    @staticmethod
    def _create_table_if_not_exists(conn):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS migraine_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date TEXT,
            Time TEXT,
            "Pain Level" INTEGER,
            Medication TEXT,
            Dosage TEXT,
            Sleep TEXT,
            "Physical Activity" TEXT,
            Triggers TEXT,
            Notes TEXT,
            Location TEXT,
            Timezone TEXT,
            Latitude REAL,
            Longitude REAL
        );
        """
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
        except Exception as e:
            print(f"Error creating table: {e}")

    @staticmethod
    def add_entry(data: dict, db_path: str):
        """
        Validates and appends a new migraine entry to the specified SQLite database.
        Raises ValueError if validation fails.
        """
        # --- Date validation ---
        date = data.get('Date', '')
        date_regex = r"^\d{4}-\d{2}-\d{2}$"
        if not re.match(date_regex, date):
            raise ValueError("Invalid date format. Please use YYYY-MM-DD.")
        
        try:
            datetime.strptime(date, "%Y-%m-%d")
        except ValueError:
             raise ValueError("Invalid date. Please enter a valid calendar date.")

        # --- Time validation ---
        time = data.get('Time', '')
        time_regex = r"^\d{2}:\d{2}$"
        if not re.match(time_regex, time):
             raise ValueError("Invalid time format. Please use HH:MM (24 hour time).")
        
        try:
            datetime.strptime(time, "%H:%M")
        except ValueError:
            raise ValueError("Invalid time. Please enter a valid time.")

        # --- Persistence (SQLite) ---
        try:
            conn = sqlite3.connect(db_path)
            EntryService._create_table_if_not_exists(conn)
            
            # Prepare SQL
            columns = ', '.join(f'"{k}"' for k in data.keys())
            placeholders = ', '.join('?' for _ in data)
            sql = f'INSERT INTO migraine_log ({columns}) VALUES ({placeholders})'
            
            cur = conn.cursor()
            cur.execute(sql, list(data.values()))
            conn.commit()
            conn.close()
        except Exception as e:
            raise ValueError(f"Database error: {e}")
            
    @staticmethod
    def get_entries_from_db(db_path: str):
        """
        Reads entries from the SQLite database.
        Returns a DataFrame.
        """
        try:
            conn = sqlite3.connect(db_path)
            query = "SELECT id, Date, Time, [Pain Level], Medication, Dosage, Sleep, [Physical Activity], Triggers, Notes, Location, Latitude, Longitude FROM migraine_log"
            data = pd.read_sql_query(query, conn)
            conn.close()
            return data
        except (sqlite3.OperationalError, pd.errors.DatabaseError) as e:
            # If table doesn't exist, return empty DataFrame
            if "no such table" in str(e):
                return pd.DataFrame(columns=["id", "Date", "Time", "Pain Level", "Medication", "Dosage", "Sleep", "Physical Activity", "Triggers", "Notes", "Location", "Latitude", "Longitude"])
            raise e
        except Exception as e:
            # Propagate or handle? For now, re-raise or let caller handle empty logic
            raise e

    @staticmethod
    def delete_entry(entry_id: int, db_path: str):
        """
        Deletes an entry by ID.
        """
        try:
            conn = sqlite3.connect(db_path)
            cursor = conn.cursor()
            cursor.execute("DELETE FROM migraine_log WHERE id = ?", (entry_id,))
            conn.commit()
            if cursor.rowcount == 0:
                 conn.close()
                 raise ValueError(f"Entry with id {entry_id} not found")
            conn.close()
        except Exception as e:
             raise ValueError(f"Database error: {e}")

    @staticmethod
    def update_entry(entry_id: int, data: dict, db_path: str):
        """
        Updates an existing entry by ID.
        """
        # Validate Date/Time again? Yes, strictly speaking we should, but assuming inputs are clean for now or reusing validation logic would be better.
        # reusing add_entry validation logic is tricky without extraction. For now, simple update.
        
        try:
            conn = sqlite3.connect(db_path)
            
            # Prepare SQL
            set_clause = ', '.join(f'"{k}" = ?' for k in data.keys())
            sql = f'UPDATE migraine_log SET {set_clause} WHERE id = ?'
            
            values = list(data.values())
            values.append(entry_id)
            
            cur = conn.cursor()
            cur.execute(sql, values)
            conn.commit()
            
            if cur.rowcount == 0:
                 conn.close()
                 raise ValueError(f"Entry with id {entry_id} not found")
                 
            conn.close()
        except Exception as e:
            raise ValueError(f"Database error: {e}")


