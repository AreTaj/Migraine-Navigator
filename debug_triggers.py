
from api.utils import get_db_path
import sqlite3
import os

def check_db():
    db_path = get_db_path()
    print(f"Checking DB at: {db_path}")
    
    if not os.path.exists(db_path):
        print("DB file not found!")
        return

    try:
        conn = sqlite3.connect(db_path)
        c = conn.cursor()
        
        # Check Triggers Table
        try:
            c.execute("SELECT count(*) FROM triggers")
            count = c.fetchone()[0]
            print(f"Triggers Count: {count}")
            
            if count > 0:
                c.execute("SELECT id, name, category FROM triggers LIMIT 5")
                rows = c.fetchall()
                print("First 5 triggers:")
                for r in rows:
                    print(r)
            else:
                print("Triggers table is EMPTY.")
                
        except Exception as e:
            print(f"Error querying triggers: {e}")
            
        conn.close()
    except Exception as e:
        print(f"Connection error: {e}")

if __name__ == "__main__":
    check_db()
