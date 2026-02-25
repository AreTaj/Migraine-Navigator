import sqlite3
import os
import sys

# Add the top-level directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.entry_service import EntryService

import unittest

class TestSchemaCheck(unittest.TestCase):
    def test_add_pressure_safely_ignored(self):
        db_path = "test_pressure_schema.db"
        if os.path.exists(db_path):
            os.remove(db_path)
            
        data = {
            'Date': '2023-10-10', 'Time': '12:00',
            'weather_pressure': 1012,
            'Pain Level': 5
        }
        
        try:
            data = EntryService.sanitize_entry(data)
            # This should succeed silently without raising OperationalError
            EntryService.add_entry(data, db_path)
        except Exception as e:
            self.fail(f"add_entry raised an exceptionally unexpectedly: {e}")
        finally:
            if os.path.exists(db_path):
                os.remove(db_path)

if __name__ == '__main__':
    unittest.main()
