import sqlite3
import os

def migrate():
    # Resolving path relative to this script:
    # script is in /scripts
    # db is in /data
    project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    db_path = os.path.join(project_root, 'data', 'migraine_log.db')
    
    print(f"Migrating database at: {db_path}")
    
    if not os.path.exists(db_path):
        print("Error: Database file not found!")
        return

    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    
    try:
        # Check if column exists
        c.execute("PRAGMA table_info(triggers)")
        columns = [row[1] for row in c.fetchall()]
        
        if 'category' in columns:
            print("Column 'category' already exists in 'triggers' table.")
        else:
            print("Adding 'category' column to 'triggers' table...")
            c.execute("ALTER TABLE triggers ADD COLUMN category TEXT")
            conn.commit()
            print("Migration successful.")
            
    except Exception as e:
        print(f"Migration failed: {e}")
    finally:
        conn.close()

if __name__ == "__main__":
    migrate()
