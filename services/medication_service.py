import sqlite3
import os
from typing import List
from api.models import Medication

class MedicationService:
    @staticmethod
    def _create_table_if_not_exists(conn):
        # Create table with new schema
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS medications (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            display_name TEXT,
            default_dosage TEXT,
            frequency TEXT DEFAULT 'as_needed',
            period_days INTEGER
        );
        """
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
            
            # Schema Migration: Add columns if they don't exist
            c.execute("PRAGMA table_info(medications)")
            cols = [info[1] for info in c.fetchall()]
            
            if 'frequency' not in cols:
                print("Migrating medications table: Adding 'frequency' column")
                c.execute("ALTER TABLE medications ADD COLUMN frequency TEXT DEFAULT 'as_needed'")
                
            if 'period_days' not in cols:
                print("Migrating medications table: Adding 'period_days' column")
                c.execute("ALTER TABLE medications ADD COLUMN period_days INTEGER")

            conn.commit()
        except Exception as e:
            print(f"Error creating medications table: {e}")

    @staticmethod
    def get_medications(db_path: str) -> List[dict]:
        try:
            conn = sqlite3.connect(db_path)
            MedicationService._create_table_if_not_exists(conn)
            
            c = conn.cursor()
            c.execute("SELECT id, name, display_name, default_dosage, frequency, period_days FROM medications")
            rows = c.fetchall()
            conn.close()
            
            meds = []
            for r in rows:
                meds.append({
                    "id": r[0],
                    "name": r[1],
                    "display_name": r[2],
                    "default_dosage": r[3],
                    "frequency": r[4],
                    "period_days": r[5]
                })
            return meds
        except Exception as e:
            raise e

    @staticmethod
    def add_medication(data: dict, db_path: str):
        try:
            conn = sqlite3.connect(db_path)
            MedicationService._create_table_if_not_exists(conn)
            
            c = conn.cursor()
            sql = "INSERT INTO medications (name, display_name, default_dosage, frequency, period_days) VALUES (?, ?, ?, ?, ?)"
            c.execute(sql, (
                data['name'], 
                data.get('display_name', ''), 
                data.get('default_dosage', ''),
                data.get('frequency', 'as_needed'),
                data.get('period_days')
            ))
            new_id = c.lastrowid
            conn.commit()
            conn.close()
            return new_id
        except sqlite3.IntegrityError:
            raise ValueError("Medication with this name already exists")
        except Exception as e:
            raise e

    @staticmethod
    def update_medication(med_id: int, data: dict, db_path: str):
        try:
            conn = sqlite3.connect(db_path)
            
            c = conn.cursor()
            sql = "UPDATE medications SET name=?, display_name=?, default_dosage=?, frequency=?, period_days=? WHERE id=?"
            c.execute(sql, (
                data['name'], 
                data.get('display_name', ''), 
                data.get('default_dosage', ''), 
                data.get('frequency', 'as_needed'),
                data.get('period_days'),
                med_id
            ))
            conn.commit()
            if c.rowcount == 0:
                conn.close()
                raise ValueError("Medication not found")
            conn.close()
        except sqlite3.IntegrityError:
            raise ValueError("Medication name collision")
        except Exception as e:
            raise e

    @staticmethod
    def delete_medication(med_id: int, db_path: str):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("DELETE FROM medications WHERE id=?", (med_id,))
            conn.commit()
            if c.rowcount == 0:
                conn.close()
                raise ValueError("Medication not found")
            conn.close()
        except Exception as e:
            raise e

    @staticmethod
    def scan_and_import_history(db_path: str) -> int:
        """
        Scans 'migraine_log' table for unique medication names and imports them
        into 'medications' table if they don't exist.
        Returns the number of new medications added.
        """
        import json
        
        try:
            conn = sqlite3.connect(db_path)
            MedicationService._create_table_if_not_exists(conn)
            c = conn.cursor()

            # 1. Get existing meds
            c.execute("SELECT name FROM medications")
            existing_meds = set(r[0].lower() for r in c.fetchall())

            # 2. Scan History
            # We need to check both Legacy 'Medication' (text) and New 'Medications' (JSON)
            found_meds = set()

            # Check if tables exist
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migraine_log'")
            if not c.fetchone():
                conn.close()
                return 0

            # Get data
            # Check if columns exist
            c.execute("PRAGMA table_info(migraine_log)")
            cols = [info[1] for info in c.fetchall()]
            
            has_legacy = 'Medication' in cols
            has_new = 'Medications' in cols
            
            if has_legacy:
                c.execute("SELECT Medication FROM migraine_log WHERE Medication IS NOT NULL AND Medication != ''")
                for row in c.fetchall():
                    # Legacy format: comma separated strings? Or just single? Assume comma
                    parts = [p.strip() for p in row[0].split(',')]
                    for p in parts:
                        if p: found_meds.add(p)
            
            if has_new:
                c.execute("SELECT Medications FROM migraine_log WHERE Medications IS NOT NULL AND Medications != ''")
                for row in c.fetchall():
                    try:
                        # JSON format: [{"name": "Advil", ...}, ...]
                        data = json.loads(row[0])
                        if isinstance(data, list):
                            for item in data:
                                if isinstance(item, dict) and 'name' in item:
                                    found_meds.add(item['name'])
                    except json.JSONDecodeError:
                        pass
            
            # 3. Insert New Meds
            added_count = 0
            for med_name in found_meds:
                if med_name.lower() not in existing_meds:
                    # Insert
                    # Default to 'as_needed'
                    clean_name = med_name.strip()
                    if not clean_name: continue
                    
                    try:
                        c.execute("INSERT INTO medications (name, frequency) VALUES (?, 'as_needed')", (clean_name,))
                        added_count += 1
                    except sqlite3.IntegrityError:
                        pass # Should catch case-sensitive duplicates if schema allowed, but we check set lower()

            conn.commit()
            conn.close()
            return added_count

        except Exception as e:
            print(f"Import Error: {e}")
            raise e
