import sqlite3
import os
import sys

# Add project root to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from services.trigger_service import TriggerService

DB_PATH = "data/migraine_log.db"

def migrate_triggers():
    print(f"Migrating triggers from {DB_PATH}...")
    
    if not os.path.exists(DB_PATH):
        print(f"Database not found at {DB_PATH}")
        return

    conn = sqlite3.connect(DB_PATH)
    c = conn.cursor()

    # 1. Check if 'triggers' column exists in 'migraine_log'
    # It might be in 'entries' or 'migraine_log' depending on previous naming consistency.
    # Looking at codebase, usually 'migraine_log'.
    
    # Actually, let's just inspect the table info to be sure
    c.execute("SELECT name FROM sqlite_master WHERE type='table' AND (name='migraine_log' OR name='entries')")
    tables = [r[0] for r in c.fetchall()]
    
    target_table = None
    if 'migraine_log' in tables: target_table = 'migraine_log'
    elif 'entries' in tables: target_table = 'entries'
    
    if not target_table:
        print("No log table found.")
        return

    print(f"Scanning table: {target_table}")
    
    # 2. Fetch all raw trigger strings
    # "triggers" column might be named "Trigger", "triggers", etc.
    c.execute(f"PRAGMA table_info({target_table})")
    cols = [r[1] for r in c.fetchall()]
    
    trigger_col = None
    for possible in ['triggers', 'Trigger', 'Triggers']:
        if possible in cols:
            trigger_col = possible
            break
            
    if not trigger_col:
        print("No 'triggers' column found in table.")
        conn.close()
        return

    c.execute(f"SELECT {trigger_col} FROM {target_table} WHERE {trigger_col} IS NOT NULL AND {trigger_col} != ''")
    rows = c.fetchall()
    
    # 3. Aggregate Usage Counts
    # Map: Trigger Name -> Count
    trigger_counts = {}
    
    for r in rows:
        raw = r[0]
        # Assume comma separated
        parts = [p.strip() for p in raw.split(',')]
        for p in parts:
            if not p: continue
            # Normalize casing slightly? 
            # Or keep user's original casing? Let's keep original but count consistently?
            # For now, simplistic approach:
            if p not in trigger_counts:
                trigger_counts[p] = 0
            trigger_counts[p] += 1
            
    print(f"Found {len(trigger_counts)} distinct triggers.")
    
    # 4. Insert into Registry using Service
    # We'll need to manually set usage count, so let's bypass add_trigger slightly or update it
    
    # Initialize the table
    TriggerService.get_triggers(DB_PATH) 
    
    # Insert loop
    c_service = conn.cursor()
    
    added = 0
    updated = 0
    
    for name, count in trigger_counts.items():
        try:
            # Try insert
            c_service.execute("INSERT INTO triggers (name, usage_count) VALUES (?, ?)", (name, count))
            added += 1
        except sqlite3.IntegrityError:
            # Already exists? Update count
            c_service.execute("UPDATE triggers SET usage_count = ? WHERE name = ?", (count, name))
            updated += 1
            
    conn.commit()
    conn.close()
    
    print(f"Migration Complete: {added} added, {updated} updated.")

if __name__ == "__main__":
    migrate_triggers()
