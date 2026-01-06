import sqlite3
import os
import json
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
            period_days INTEGER,
            usage_count INTEGER DEFAULT 0
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

            if 'usage_count' not in cols:
                print("Migrating medications table: Adding 'usage_count' column")
                c.execute("ALTER TABLE medications ADD COLUMN usage_count INTEGER DEFAULT 0")

            conn.commit()
        except Exception as e:
            print(f"Error creating medications table: {e}")

    @staticmethod
    def get_medications(db_path: str) -> List[dict]:
        try:
            conn = sqlite3.connect(db_path)
            MedicationService._create_table_if_not_exists(conn)
            
            c = conn.cursor()
            # Sort by usage_count DESC so most used meds appear first
            c.execute("SELECT id, name, display_name, default_dosage, frequency, period_days, usage_count FROM medications ORDER BY usage_count DESC, name ASC")
            rows = c.fetchall()
            
            # --- AUTO-MIGRATION & SYNC (Zero usage check) ---
            # If we return rows but TOTAL usage is 0, we might need to sync history (like TriggerService)
            total_usage = sum((r[6] or 0) for r in rows) if rows else 0
            if rows and total_usage == 0:
                print("Medications exist but usage is 0. Syncing counts from history...")
                try:
                    # Check for historical tables
                    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migraine_log'")
                    if c.fetchone():
                        # Determine columns available
                        c.execute("PRAGMA table_info(migraine_log)")
                        log_cols = [info[1] for info in c.fetchall()]
                        has_legacy = 'Medication' in log_cols
                        has_new = 'Medications' in log_cols
                        
                        counts = {}

                        # 1. Scan Legacy
                        if has_legacy:
                            c.execute("SELECT Medication FROM migraine_log WHERE Medication IS NOT NULL AND Medication != ''")
                            for (raw_str,) in c.fetchall():
                                parts = [p.strip() for p in raw_str.split(',') if p.strip()]
                                for p in parts:
                                    counts[p] = counts.get(p, 0) + 1
                        
                        # 2. Scan New JSON format
                        if has_new:
                            c.execute("SELECT Medications FROM migraine_log WHERE Medications IS NOT NULL AND Medications != ''")
                            for (json_str,) in c.fetchall():
                                try:
                                    data = json.loads(json_str)
                                    if isinstance(data, list):
                                        for item in data:
                                            if isinstance(item, dict) and 'name' in item:
                                                name = item['name']
                                                counts[name] = counts.get(name, 0) + 1
                                except json.JSONDecodeError:
                                    pass

                        if counts:
                            for m_name, count in counts.items():
                                # We update by name. Note: User might have logged "Advil" and "advil", match implies case sensitivity depending on DB collation or exact string.
                                # For safety, we try exact match first
                                c.execute("UPDATE medications SET usage_count = ? WHERE name = ?", (count, m_name))
                            
                            conn.commit()
                            # Re-fetch after sync
                            c.execute("SELECT id, name, display_name, default_dosage, frequency, period_days, usage_count FROM medications ORDER BY usage_count DESC, name ASC")
                            rows = c.fetchall()
                except Exception as sync_err:
                    print(f"Medication usage sync failed: {sync_err}")
            # ------------------------------------------------

            conn.close()
            
            meds = []
            for r in rows:
                meds.append({
                    "id": r[0],
                    "name": r[1],
                    "display_name": r[2],
                    "default_dosage": r[3],
                    "frequency": r[4],
                    "period_days": r[5],
                    "usage_count": r[6]
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
            sql = "INSERT INTO medications (name, display_name, default_dosage, frequency, period_days, usage_count) VALUES (?, ?, ?, ?, ?, 0)"
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
    def increment_usage(med_names: List[str], db_path: str):
        """
        Increments usage count for a list of medication names.
        """
        if not med_names: return

        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            for name in med_names:
                # Permissive update
                c.execute("UPDATE medications SET usage_count = usage_count + 1 WHERE name = ?", (name.strip(),))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error incrementing medication usage: {e}")

    @staticmethod
    def scan_and_import_history(db_path: str) -> int:
        """
        Scans 'migraine_log' table for unique medication names and imports them
        into 'medications' table if they don't exist.
        Returns the number of new medications added.
        """
        try:
            conn = sqlite3.connect(db_path)
            MedicationService._create_table_if_not_exists(conn)
            c = conn.cursor()

            # 1. Get existing meds
            c.execute("SELECT name FROM medications")
            existing_meds = set(r[0].lower() for r in c.fetchall())

            # 2. Scan History
            found_meds = set()

            # Check if tables exist
            c.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='migraine_log'")
            if not c.fetchone():
                conn.close()
                return 0

            # Get data
            c.execute("PRAGMA table_info(migraine_log)")
            cols = [info[1] for info in c.fetchall()]
            
            has_legacy = 'Medication' in cols
            has_new = 'Medications' in cols
            
            if has_legacy:
                c.execute("SELECT Medication FROM migraine_log WHERE Medication IS NOT NULL AND Medication != ''")
                for row in c.fetchall():
                    parts = [p.strip() for p in row[0].split(',')]
                    for p in parts:
                        if p: found_meds.add(p)
            
            if has_new:
                c.execute("SELECT Medications FROM migraine_log WHERE Medications IS NOT NULL AND Medications != ''")
                for row in c.fetchall():
                    try:
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
                    clean_name = med_name.strip()
                    if not clean_name: continue
                    
                    try:
                        # Initialize new imports with 0 usage (or we could calculate it here, but get_medications syncs it anyway)
                        c.execute("INSERT INTO medications (name, frequency, usage_count) VALUES (?, 'as_needed', 0)", (clean_name,))
                        added_count += 1
                        existing_meds.add(clean_name.lower()) # Prevent dups in loop
                    except sqlite3.IntegrityError:
                        pass 

            conn.commit()
            conn.close()
            return added_count

        except Exception as e:
            print(f"Import Error: {e}")
            raise e
