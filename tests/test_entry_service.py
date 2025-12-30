import unittest
import os
import sqlite3
import pandas as pd
import sys

# Add the top-level directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.entry_service import EntryService

class TestEntryService(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_entry_service.db"
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def tearDown(self):
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_validation_invalid_date(self):
        data = {'Date': '10-10-2023', 'Time': '12:00'}
        with self.assertRaises(ValueError) as cm:
            EntryService.add_entry(data, self.db_path)
        self.assertIn("Invalid date format", str(cm.exception))

    def test_validation_invalid_time(self):
        data = {'Date': '2023-10-10', 'Time': '1200'}
        with self.assertRaises(ValueError) as cm:
             EntryService.add_entry(data, self.db_path)
        self.assertIn("Invalid time format", str(cm.exception))

    def test_persistence_creates_table_and_inserts(self):
        data = {
            'Date': '2023-10-10',
            'Time': '12:00',
            'Pain Level': 5,
            'Medication': 'Advil',
            'Dosage': '200mg',
            'Sleep': 'Good',
            'Physical Activity': 'None',
            'Triggers': 'Stress',
            'Notes': 'Test Note',
            'Location': 'Home',
            'Timezone': 'EST',
            'Latitude': 1.0,
            'Longitude': 1.0
        }
        
        EntryService.add_entry(data, self.db_path)
        
        # Verify directly via sqlite
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        args = conn.execute("SELECT * FROM migraine_log").fetchone()
        conn.close()
        
        self.assertEqual(args['Notes'], 'Test Note')
        self.assertEqual(args['Pain Level'], 5)

    def test_retrieval_success(self):
        # Insert data first
        data = {
           'Date': '2023-10-10', 'Time': '12:00', 'Pain Level': 5,
           'Medication': '', 'Dosage': '', 'Sleep': '', 'Physical Activity': '',
           'Triggers': '', 'Notes': 'Retrieved', 'Location': '', 'Timezone': '',
           'Latitude': 0, 'Longitude': 0
        }
        EntryService.add_entry(data, self.db_path)
        
        entries = EntryService.get_entries_from_db(self.db_path)
        self.assertIsInstance(entries, list)
        self.assertEqual(len(entries), 1)
        self.assertEqual(entries[0]['Notes'], 'Retrieved')

    def test_retrieval_no_table(self):
        # Should return empty list, not raise error
        entries = EntryService.get_entries_from_db(self.db_path)
        self.assertIsInstance(entries, list)
        self.assertEqual(len(entries), 0)

if __name__ == '__main__':
    unittest.main()
