import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os
import sqlite3
import sys
from tkinter import Tk

# Add the top-level directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from input.input_frame import InputFrame

class TestInputFrame(unittest.TestCase):
    def setUp(self):
        self.db_path = "test_migraine_log.db"
        self.root = Tk()
        self.input_frame = InputFrame(self.root, self.db_path)
        self.input_frame.grid_widgets()

    def tearDown(self):
        self.root.destroy()
        if os.path.exists(self.db_path):
            os.remove(self.db_path)

    def test_fill_time_and_date(self):
        self.input_frame.fill_time_and_date()
        now = datetime.now()
        self.assertEqual(self.input_frame.date_entry.get(), now.strftime("%Y-%m-%d"))
        self.assertEqual(self.input_frame.time_entry.get(), now.strftime("%H:%M"))

    # Patch objects where they are used (in input.input_frame)
    @patch('input.input_frame.get_location_from_ip', return_value=((40.7128, -74.0060), "New York, NY"))
    @patch('input.input_frame.get_local_timezone', return_value=MagicMock(key="America/New_York"))
    def test_save_entry(self, mock_get_local_timezone, mock_get_location_from_ip):
        # Set test data
        self.input_frame.date_entry.insert(0, "2023-10-10")
        self.input_frame.time_entry.insert(0, "12:00")
        self.input_frame.pain_level_scale.set(5)
        self.input_frame.medication_entry.insert(0, "Ibuprofen")
        self.input_frame.dosage_entry.insert(0, "200mg")
        self.input_frame.sleep_var.set("fair")
        self.input_frame.physical_activity_var.set("moderate")
        self.input_frame.triggers_entry.insert("1.0", "Stress")
        self.input_frame.notes_entry.insert("1.0", "TEST")
        self.input_frame.location_var.set("automatic")

        # Mock the view_frame's update_entries method
        mock_view_frame = MagicMock()
        
        # Call save_entry
        self.input_frame.save_entry(mock_view_frame)

        # Check if the file was created and contains the correct data
        conn = sqlite3.connect(self.db_path)
        conn.row_factory = sqlite3.Row
        cur = conn.cursor()
        cur.execute("SELECT * FROM migraine_log")
        rows = cur.fetchall()
        conn.close()
        
        self.assertEqual(len(rows), 1)
        row = rows[0]
        self.assertEqual(row['Date'], "2023-10-10")
        self.assertEqual(row['Time'], "12:00")
        self.assertEqual(row['Pain Level'], 5) # stored as int/real in DB
        self.assertEqual(row['Medication'], "Ibuprofen")
        self.assertEqual(row['Dosage'], "200mg")
        self.assertEqual(row['Sleep'], "fair")
        self.assertEqual(row['Physical Activity'], "moderate")
        self.assertEqual(row['Triggers'], "Stress")
        self.assertEqual(row['Notes'], "TEST")
        self.assertEqual(row['Location'], "New York, NY")
        self.assertEqual(row['Latitude'], 40.7128)
        self.assertEqual(row['Longitude'], -74.0060)
        self.assertEqual(row['Timezone'], "America/New_York")

        # Check if the view_frame's update_entries method was called
        mock_view_frame.update_entries.assert_called_once()

if __name__ == '__main__':
    unittest.main()