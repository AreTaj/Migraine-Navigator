import csv
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
            query = "SELECT Date, Time, [Pain Level], Medication, Dosage, Sleep, [Physical Activity], Triggers, Notes, Location FROM migraine_log"
            data = pd.read_sql_query(query, conn)
            conn.close()
            return data
        except (sqlite3.OperationalError, pd.errors.DatabaseError) as e:
            # If table doesn't exist, return empty DataFrame
            if "no such table" in str(e):
                return pd.DataFrame(columns=["Date", "Time", "Pain Level", "Medication", "Dosage", "Sleep", "Physical Activity", "Triggers", "Notes", "Location"])
            raise e
        except Exception as e:
            # Propagate or handle? For now, re-raise or let caller handle empty logic
            raise e

    @staticmethod
    def get_entries_from_csv(csv_path: str):
         """
         Reads entries from CSV. 
         (Added this as a fallback/fix since InputFrame writes to CSV)
         """
         try:
             return pd.read_csv(csv_path).fillna("")
         except FileNotFoundError:
             return pd.DataFrame()
