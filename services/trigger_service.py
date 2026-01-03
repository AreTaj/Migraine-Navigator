import sqlite3
import os
from typing import List, Optional

class TriggerService:
    @staticmethod
    def _create_table_if_not_exists(conn):
        create_table_sql = """
        CREATE TABLE IF NOT EXISTS triggers (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            usage_count INTEGER DEFAULT 0,
            is_system_default BOOLEAN DEFAULT 0,
            category TEXT
        );
        """
        try:
            c = conn.cursor()
            c.execute(create_table_sql)
            conn.commit()
        except Exception as e:
            print(f"Error creating triggers table: {e}")

    @staticmethod
    def get_triggers(db_path: str) -> List[dict]:
        try:
            conn = sqlite3.connect(db_path)
            TriggerService._create_table_if_not_exists(conn)
            
            c = conn.cursor()
            # Order by usage count (most popular first)
            c.execute("SELECT id, name, usage_count, is_system_default, category FROM triggers ORDER BY usage_count DESC, name ASC")
            rows = c.fetchall()

            # --- AUTO-MIGRATION & SYNC ---
            # 1. Fresh Migration (Registry Empty)
            if not rows:
                print("Triggers registry empty. Auto-migrating...")
                try:
                    c.execute("SELECT Triggers FROM migraine_log WHERE Triggers IS NOT NULL AND Triggers != ''")
                    entry_rows = c.fetchall()
                    
                    counts = {}
                    for (raw_str,) in entry_rows:
                        if raw_str:
                            parts = [p.strip() for p in raw_str.split(',') if p.strip()]
                            for p in parts:
                                counts[p] = counts.get(p, 0) + 1
                            
                    if counts:
                        print(f"Found {len(counts)} unique triggers. Importing with counts...")
                        for t_name, count in counts.items():
                            try:
                                c.execute("INSERT INTO triggers (name, usage_count, category) VALUES (?, ?, NULL)", (t_name, count))
                            except sqlite3.IntegrityError:
                                pass 
                        conn.commit()
                        # Re-fetch
                        c.execute("SELECT id, name, usage_count, is_system_default, category FROM triggers ORDER BY usage_count DESC, name ASC")
                        rows = c.fetchall()
                except Exception as mig_err:
                    print(f"Migration failed: {mig_err}")

            # 2. Fix Zero-Counts (Registry Exists but counts logic was missed)
            # If we have triggers but TOTAL usage is 0, it's suspicious given we have history.
            total_usage = sum(r[2] for r in rows) if rows else 0
            if rows and total_usage == 0:
                print("Triggers exist but usage is 0. Syncing counts from history...")
                try:
                    c.execute("SELECT Triggers FROM migraine_log WHERE Triggers IS NOT NULL AND Triggers != ''")
                    entry_rows = c.fetchall()
                    
                    counts = {}
                    for (raw_str,) in entry_rows:
                        if raw_str:
                            parts = [p.strip() for p in raw_str.split(',') if p.strip()]
                            for p in parts:
                                counts[p] = counts.get(p, 0) + 1
                    
                    if counts:
                        for t_name, count in counts.items():
                            c.execute("UPDATE triggers SET usage_count = ? WHERE name = ?", (count, t_name))
                        conn.commit()
                        # Re-fetch
                        c.execute("SELECT id, name, usage_count, is_system_default, category FROM triggers ORDER BY usage_count DESC, name ASC")
                        rows = c.fetchall()
                except Exception as sync_err:
                    print(f"Sync failed: {sync_err}")
            # -------------------------------------------------------------------

            conn.close()
            
            triggers = []
            for r in rows:
                triggers.append({
                    "id": r[0],
                    "name": r[1],
                    "usage_count": r[2],
                    "is_system_default": bool(r[3]),
                    "category": r[4]
                })
            return triggers
        except Exception as e:
            raise e

    @staticmethod
    def add_trigger(name: str, db_path: str, category: Optional[str] = None) -> int:
        clean_name = name.strip()
        if not clean_name:
            raise ValueError("Trigger name cannot be empty")
            
        try:
            conn = sqlite3.connect(db_path)
            TriggerService._create_table_if_not_exists(conn)
            
            c = conn.cursor()
            c.execute("INSERT INTO triggers (name, usage_count, category) VALUES (?, 0, ?)", (clean_name, category))
            new_id = c.lastrowid
            conn.commit()
            conn.close()
            return new_id
        except sqlite3.IntegrityError:
            raise ValueError("Trigger with this name already exists")
        except Exception as e:
            raise e

    @staticmethod
    def update_trigger(trigger_id: int, db_path: str, category: Optional[str] = None, name: Optional[str] = None):
        try:
            conn = sqlite3.connect(db_path)
            # Enable row factory for easier access if needed, though cursor is fine
            c = conn.cursor()
            
            # --- CASCADING RENAME LOGIC ---
            # 1. Fetch current name BEFORE update
            old_name = None
            if name is not None:
                c.execute("SELECT name FROM triggers WHERE id = ?", (trigger_id,))
                row = c.fetchone()
                if row:
                    old_name = row[0]
                else:
                    conn.close()
                    raise ValueError("Trigger not found")

            updates = []
            params = []
            
            if category is not None:
                updates.append("category = ?")
                params.append(category)
            
            if name is not None:
                cleaned_name = name.strip()
                if not cleaned_name:
                    conn.close()
                    raise ValueError("Trigger name cannot be empty")
                updates.append("name = ?")
                params.append(cleaned_name)
                
            if not updates:
                conn.close()
                return # No updates needed
                
            params.append(trigger_id)
            query = f"UPDATE triggers SET {', '.join(updates)} WHERE id = ?"
            
            try:
                c.execute(query, tuple(params))
                # Don't commit yet, we might need to update history
            except sqlite3.IntegrityError:
                conn.close()
                raise ValueError("Trigger with this name already exists")
                
            if c.rowcount == 0:
                conn.close()
                raise ValueError("Trigger not found")
            
            # 2. Update historical logs if name changed
            if name is not None and old_name and name != old_name:
                # Find all entries containing the old name
                # Use a specific lookup to avoid partial matches on substrings if possible, 
                # but LIKE %old_name% is the starting point
                c.execute("SELECT id, Triggers FROM migraine_log WHERE Triggers LIKE ?", (f"%{old_name}%",))
                history_rows = c.fetchall()
                
                for row_id, raw_triggers in history_rows:
                    if not raw_triggers: 
                        continue
                    
                    # Split, Replace, Rejoin
                    t_list = [t.strip() for t in raw_triggers.split(',')]
                    
                    # Exact match replacement
                    modified = False
                    new_list = []
                    for t in t_list:
                        # Case-sensitive match on the old name to be safe, 
                        # or could be case-insensitive if we want to clean up variations
                        if t == old_name:
                            new_list.append(name.strip())
                            modified = True
                        else:
                            new_list.append(t)
                    
                    if modified:
                        new_triggers_str = ", ".join(new_list)
                        c.execute("UPDATE migraine_log SET Triggers = ? WHERE id = ?", (new_triggers_str, row_id))

            conn.commit()
            conn.close()
        except Exception as e:
            raise e

    @staticmethod
    def delete_trigger(trigger_id: int, db_path: str):
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("DELETE FROM triggers WHERE id=?", (trigger_id,))
            conn.commit()
            if c.rowcount == 0:
                conn.close()
                raise ValueError("Trigger not found")
            conn.close()
        except Exception as e:
            raise e

    @staticmethod
    def increment_usage(trigger_names: List[str], db_path: str):
        """
        Increments usage count for a list of trigger names.
        """
        if not trigger_names: return
        
        try:
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            for name in trigger_names:
                # We use a permissive update (if it exists)
                c.execute("UPDATE triggers SET usage_count = usage_count + 1 WHERE name = ?", (name.strip(),))
            conn.commit()
            conn.close()
        except Exception as e:
            print(f"Error incrementing trigger usage: {e}")
