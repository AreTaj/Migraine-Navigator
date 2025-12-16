import os
import re
import sqlite3
import pandas as pd
import json
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
            Medications TEXT,  -- New JSON column
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
            
            # Check if 'Medications' column exists (for existing DBs)
            c.execute("PRAGMA table_info(migraine_log)")
            columns = [info[1] for info in c.fetchall()]
            if 'Medications' not in columns:
                print("Adding 'Medications' column to schema...")
                c.execute("ALTER TABLE migraine_log ADD COLUMN Medications TEXT")
                conn.commit()
                # Run Migration immediately
                EntryService.migrate_legacy_medications(conn)
                
        except Exception as e:
            print(f"Error creating/updating table: {e}")

    @staticmethod
    def migrate_legacy_medications(conn):
        """
        Migrates legacy 'Medication' and 'Dosage' text fields into the 'Medications' JSON column.
        Only runs for rows where 'Medications' is NULL and legacy 'Medication' is populated.
        """
        print("Running legacy medication migration...")
        try:
            c = conn.cursor()
            c.execute("SELECT id, Medication, Dosage FROM migraine_log WHERE Medications IS NULL AND Medication != '' AND Medication IS NOT NULL")
            rows = c.fetchall()
            
            for row in rows:
                entry_id, med, dosage = row
                # Create rudimentary JSON list
                med_list = [{"name": med, "dosage": dosage or ""}]
                json_str = json.dumps(med_list)
                
                c.execute("UPDATE migraine_log SET Medications = ? WHERE id = ?", (json_str, entry_id))
            
            conn.commit()
            print(f"Migrated {len(rows)} entries.")
        except Exception as e:
            print(f"Migration failed: {e}")

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

        # --- Handle Medications JSON ---
        if 'Medications' in data and isinstance(data['Medications'], list):
            data['Medications'] = json.dumps(data['Medications'])
        
        # Ensure legacy columns are empty for new entries (or could populate first med for compat)
        # Choosing to keep them empty to signify deprecation
        if 'Medication' not in data: data['Medication'] = ""
        if 'Dosage' not in data: data['Dosage'] = ""

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
    def get_entries_from_db(db_path: str, start_date: str = None, end_date: str = None):
        """
        Reads entries from the SQLite database.
        Optional: Filter by date range (inclusive). Dates should be 'YYYY-MM-DD'.
        Returns a DataFrame.
        """
        try:
            conn = sqlite3.connect(db_path)
            # Ensure schema is up to date on read too
            EntryService._create_table_if_not_exists(conn)
            
            query = "SELECT * FROM migraine_log"
            params = []
            
            # Dynamic WHERE clause
            conditions = []
            if start_date:
                conditions.append("Date >= ?")
                params.append(start_date)
            if end_date:
                conditions.append("Date <= ?")
                params.append(end_date)
            
            if conditions:
                query += " WHERE " + " AND ".join(conditions)
                
            # Always sort by Date descending for History view
            query += " ORDER BY Date DESC, Time DESC"

            data = pd.read_sql_query(query, conn, params=params)
            conn.close()
            
            # Parse JSON column back to objects
            if 'Medications' in data.columns:
                def parse_meds(x):
                    if not x: return []
                    try:
                        return json.loads(x)
                    except:
                        return []
                data['Medications'] = data['Medications'].apply(parse_meds)
                
            return data
        except (sqlite3.OperationalError, pd.errors.DatabaseError) as e:
            # If table doesn't exist, return empty DataFrame
            if "no such table" in str(e):
                return pd.DataFrame()
            raise e
        except Exception as e:
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
            # --- Handle Medications JSON ---
            if 'Medications' in data and isinstance(data['Medications'], list):
                data['Medications'] = json.dumps(data['Medications'])
            
            conn = sqlite3.connect(db_path)
            EntryService._create_table_if_not_exists(conn)
            
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


