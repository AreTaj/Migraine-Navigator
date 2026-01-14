import unittest
import os
import sqlite3
import datetime
from unittest.mock import patch
import sys

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from api.utils import get_db_path

class TestUtils(unittest.TestCase):
    def setUp(self):
        self.test_db = 'test_synthetic_aging.db'
        
    def tearDown(self):
        if os.path.exists(self.test_db):
            os.remove(self.test_db)
            
    @patch('api.utils.get_data_dir')
    def test_auto_date_shifting(self, mock_data_dir):
        # 1. Setup a "Stale" Database (Last entry = 10 days ago)
        mock_data_dir.return_value = os.getcwd() # Use current dir for test
        
        conn = sqlite3.connect(self.test_db)
        c = conn.cursor()
        c.execute("CREATE TABLE migraine_log (id INTEGER PRIMARY KEY, Date TEXT)")
        
        # Create a date 10 days in the past
        ten_days_ago = (datetime.date.today() - datetime.timedelta(days=10)).strftime("%Y-%m-%d")
        eleven_days_ago = (datetime.date.today() - datetime.timedelta(days=11)).strftime("%Y-%m-%d")
        
        c.execute("INSERT INTO migraine_log (Date) VALUES (?)", (ten_days_ago,))
        c.execute("INSERT INTO migraine_log (Date) VALUES (?)", (eleven_days_ago,))
        conn.commit()
        conn.close()
        
        # Rename to expected synthetic filename for the test
        real_synthetic_name = 'synthetic_migraine_log.db'
        if os.path.exists(real_synthetic_name):
            os.rename(real_synthetic_name, real_synthetic_name + '.bak')
            
        os.rename(self.test_db, real_synthetic_name)
        
        try:
            # 2. Call get_db_path in tester mode
            # This should trigger the fresh check and update
            # We mock 'os.path.join' effectively by controlling get_data_dir and the file placement
            
            db_path = get_db_path(tester_mode=True)
            
            # 3. Verify Dates Shifted
            conn = sqlite3.connect(db_path)
            c = conn.cursor()
            c.execute("SELECT MAX(Date) FROM migraine_log")
            new_max_date = c.fetchone()[0]
            conn.close()
            
            print(f"Old Max: {ten_days_ago}")
            print(f"New Max: {new_max_date}")
            print(f"Target : {datetime.date.today().strftime('%Y-%m-%d')}")
            
            self.assertEqual(new_max_date, datetime.date.today().strftime("%Y-%m-%d"))
            
        finally:
            # Cleanup
            if os.path.exists(real_synthetic_name):
                os.remove(real_synthetic_name)
            if os.path.exists(real_synthetic_name + '.bak'):
                os.rename(real_synthetic_name + '.bak', real_synthetic_name)

if __name__ == '__main__':
    unittest.main()
