import sys
import os
import appdirs

def get_data_dir():
    """
    Returns the writable data directory.
    """
    if getattr(sys, 'frozen', False):
        # Production: Use User Data Directory
        # e.g., /Users/User/Library/Application Support/AreTaj/MigraineNavigator
        app_data = appdirs.user_data_dir("MigraineNavigator", "AreTaj")
        os.makedirs(app_data, exist_ok=True)
        return app_data
    else:
        # Development: Use local project data folder
        # api/utils.py -> .. -> .. -> data
        return os.path.join(os.path.dirname(__file__), '..', 'data')

def get_db_path(tester_mode=False):
    """
    Returns the path to the SQLite database.
    If tester_mode is True, returns path to synthetic.db (creating it if needed).
    """
    if tester_mode:
        synthetic_db = os.path.join(get_data_dir(), 'synthetic_migraine_log.db')
        # Check if we need to initialize it from CSV
        if not os.path.exists(synthetic_db):
            try:
                import pandas as pd
                import sqlite3
                import json
                
                csv_path = os.path.join(get_data_dir(), 'synthetic_migraine_log.csv')
                if os.path.exists(csv_path):
                    print(f"Initializing synthetic DB from {csv_path}...")
                    conn = sqlite3.connect(synthetic_db)
                    c = conn.cursor()
                    
                    # 1. Create Table with correct Schema (ID Primary Key is crucial)
                    # Schema matches EntryService
                    c.execute("""
                    CREATE TABLE IF NOT EXISTS migraine_log (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        Date TEXT,
                        Time TEXT,
                        "Pain Level" INTEGER,
                        Medication TEXT,
                        Dosage TEXT,
                        Medications TEXT,
                        Sleep TEXT,
                        "Physical Activity" TEXT,
                        Triggers TEXT,
                        Notes TEXT,
                        Location TEXT,
                        Timezone TEXT,
                        Latitude REAL,
                        Longitude REAL
                    );
                    """)
                    
                    # Create Medications Registry Table
                    c.execute("""
                    CREATE TABLE IF NOT EXISTS medications (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        name TEXT UNIQUE,
                        display_name TEXT,
                        default_dosage TEXT,
                        category TEXT,
                        is_preventative BOOLEAN DEFAULT 0,
                        frequency TEXT DEFAULT 'as_needed'
                    );
                    """)
                    conn.commit()
                    
                    # 2. Load and Transform CSV
                    df = pd.read_csv(csv_path)
                    
                    # --- POPULATE MEDICATIONS TABLE ---
                    # Extract unique meds and populate the registry so the page isn't blank
                    unique_meds = df[['Medication', 'Dosage']].dropna(subset=['Medication']).drop_duplicates(subset=['Medication'])
                    
                    for _, row in unique_meds.iterrows():
                        med_name = row['Medication']
                        dosage = row['Dosage'] if pd.notna(row['Dosage']) else ""
                        
                        # Simple Heuristic for Categorization
                        is_preventative = 0
                        category = "Acute"
                        frequency = "as_needed"
                        
                        if "Beta Blocker" in med_name or "Topiramate" in med_name or "Amitriptyline" in med_name or "Propranolol" in med_name:
                            is_preventative = 1
                            category = "Preventative"
                            frequency = "daily"
                        elif "Triptan" in med_name or "Sumatriptan" in med_name:
                            category = "Triptan"
                        elif "Ibuprofen" in med_name or "Advil" in med_name or "Tylenol" in med_name or "Naproxen" in med_name or "Excedrin" in med_name:
                            category = "NSAID"
                            
                        try:
                            c.execute("""
                                INSERT OR IGNORE INTO medications (name, display_name, default_dosage, category, is_preventative, frequency)
                                VALUES (?, ?, ?, ?, ?, ?)
                            """, (med_name, med_name, dosage, category, is_preventative, frequency))
                        except Exception as e:
                            print(f"Failed to insert med {med_name}: {e}")
                    
                    conn.commit()
                    # ----------------------------------
                    
                    # Transform Legacy Medication columns to JSON
                    def create_med_json(row):
                        med = row.get('Medication')
                        dosage = row.get('Dosage')
                        if pd.notna(med) and med != "":
                            return json.dumps([{"name": med, "dosage": dosage if pd.notna(dosage) else ""}])
                        return json.dumps([])

                    df['Medications'] = df.apply(create_med_json, axis=1)
                    
                    # Ensure other columns exist
                    required_cols = ["Date", "Time", "Pain Level", "Medication", "Dosage", "Sleep", "Physical Activity", 
                                     "Triggers", "Notes", "Location", "Timezone", "Latitude", "Longitude"]
                                     
                    for col in required_cols:
                        if col not in df.columns:
                            df[col] = None # Fill missing schema cols with NULL
                            
                    # 3. Append to DB
                    # Filter only columns that exist in the table to avoid unexpected errors
                    df.to_sql('migraine_log', conn, if_exists='append', index=False)
                    conn.close()
            except Exception as e:
                print(f"Failed to create synthetic DB: {e}")
                # Cleanup if failed
                if os.path.exists(synthetic_db):
                    os.remove(synthetic_db)
        # 4. Freshness Check & Auto-Shift
        # Ensure the synthetic data looks "live" by shifting dates so the last entry is today/yesterday.
        if os.path.exists(synthetic_db):
            try:
                import sqlite3
                import datetime
                
                conn = sqlite3.connect(synthetic_db)
                # Use EXCLUSIVE transaction to prevent race conditions (multiple requests shifting simultaneously)
                c = conn.cursor()
                try:
                    c.execute("BEGIN EXCLUSIVE")
                    
                    # Get max date
                    c.execute("SELECT MAX(Date) FROM migraine_log")
                    max_date_str = c.fetchone()[0]
                    
                    if max_date_str:
                        max_date = datetime.datetime.strptime(max_date_str, "%Y-%m-%d").date()
                        today = datetime.date.today()
                        
                        days_diff = (today - max_date).days
                        
                        # Shift if stats are stale OR in the future (self-correction)
                        # We allow a small buffer (e.g. 0 days) to avoid pointless 0-day shifts
                        if days_diff != 0:
                            print(f"Synthetic data drift: {days_diff} days. Shifting...")
                            
                            # Construct modifier string carefully to avoid "+-10 days" syntax
                            modifier = f"{days_diff} days"
                            if days_diff > 0:
                                modifier = f"+{days_diff} days"
                                
                            # SQLite 'date' function modifier: '+N days' or '-N days'
                            c.execute(f"UPDATE migraine_log SET Date = date(Date, '{modifier}')")
                            conn.commit()
                            print(f"Dates shifted by {modifier}.")
                        else:
                            conn.commit() # Release lock
                    else:
                        conn.commit()
                except Exception as e:
                    print(f"Lock/Shift failed: {e}")
                    conn.rollback()
                        
                conn.close()
            except Exception as e:
                print(f"Warning: Failed to auto-shift synthetic dates: {e}")

        return synthetic_db
        
    return os.path.join(get_data_dir(), 'migraine_log.db')
