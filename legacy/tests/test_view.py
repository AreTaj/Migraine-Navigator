import unittest
from unittest.mock import patch, MagicMock
import os
import pandas as pd
import sys
import sqlite3
from tkinter import Tk

# Add the top-level directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from view.view_frame import ViewFrame
from services.entry_service import EntryService

class TestViewFrame(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_migraine_log.db"
        
        # Ensure clean state
        if os.path.exists(self.db_path):
            os.remove(self.db_path)
            
        self.root = Tk()
        # Initialize with DB path
        self.view_frame = ViewFrame(self.root, self.db_path)
        self.view_frame.pack()

    def tearDown(self):
        self.root.destroy()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def _create_dummy_data(self):
        conn = sqlite3.connect(self.db_path)
        EntryService._create_table_if_not_exists(conn)
        cursor = conn.cursor()
        data = {
            'Date': '2023-10-10',
            'Time': '12:00',
            'Pain Level': 5,
            'Medication': 'Ibuprofen',
            'Dosage': '200mg',
            'Sleep': 'Fair',
            'Physical Activity': 'Moderate',
            'Triggers': 'Stress',
            'Notes': 'Had a stressful day.',
            'Location': 'New York, NY',
            'Timezone': 'EST',
            'Latitude': 40.71,
            'Longitude': -74.00
        }
        columns = ', '.join(f'"{k}"' for k in data.keys())
        placeholders = ', '.join('?' for _ in data)
        sql = f'INSERT INTO migraine_log ({columns}) VALUES ({placeholders})'
        cursor.execute(sql, list(data.values()))
        conn.commit()
        conn.close()

    def test_load_entries_no_data(self):
        # Setup creates empty DB by default (via ViewFrame init calling code eventually, or we ensure it's empty)
        # Actually ViewFrame.load_entries calls EntryService which reads. 
        # If DB doesn't exist, pandas.read_sql might fail or we need to ensure table exists.
        # EntryService.get_entries_from_db will fail if table doesn't exist.
        
        # Let's ensure table exists but is empty
        conn = sqlite3.connect(self.db_path)
        EntryService._create_table_if_not_exists(conn)
        conn.close()

        self.view_frame.load_entries()
        
        # Check if the Treeview is empty
        self.assertEqual(len(self.view_frame.entries_treeview.get_children()), 0)

    def test_load_entries_with_data(self):
        self._create_dummy_data()
        
        self.view_frame.load_entries()
        
        # Check if the Treeview has one entry
        self.assertEqual(len(self.view_frame.entries_treeview.get_children()), 1)

    def test_update_entries(self):
        self._create_dummy_data()
        
        self.view_frame.update_entries()
        
        # Check if the Treeview has one entry
        self.assertEqual(len(self.view_frame.entries_treeview.get_children()), 1)

if __name__ == '__main__':
    unittest.main()