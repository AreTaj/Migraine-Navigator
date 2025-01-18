import unittest
from unittest.mock import patch, MagicMock
from datetime import datetime
import os
import csv
import sys
from tkinter import Tk

# Add the top-level directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from input.input_frame import InputFrame

class TestInputFrame(unittest.TestCase):
    def setUp(self):
        self.root = Tk()
        self.input_frame = InputFrame(self.root, "test_migraine_log.csv")
        self.input_frame.grid_widgets()

    def tearDown(self):
        self.root.destroy()
        if os.path.exists("test_migraine_log.csv"):
            os.remove("test_migraine_log.csv")

    def test_fill_time_and_date(self):
        self.input_frame.fill_time_and_date()
        now = datetime.now()
        self.assertEqual(self.input_frame.date_entry.get(), now.strftime("%Y-%m-%d"))
        self.assertEqual(self.input_frame.time_entry.get(), now.strftime("%H:%M"))

    @patch('input.input_frame.get_location_from_ip', return_value=((40.7128, -74.0060), "New York, NY"))
    @patch('input.input_frame.get_local_timezone', return_value="America/New_York")
    def test_save_entry(self, mock_get_location_from_ip, mock_get_local_timezone):
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
        with open("test_migraine_log.csv", 'r') as csvfile:
            reader = csv.DictReader(csvfile)
            rows = list(reader)
            self.assertEqual(len(rows), 1)
            self.assertEqual(rows[0]['Date'], "2023-10-10")
            self.assertEqual(rows[0]['Time'], "12:00")
            self.assertEqual(rows[0]['Pain Level'], "5")
            self.assertEqual(rows[0]['Medication'], "Ibuprofen")
            self.assertEqual(rows[0]['Dosage'], "200mg")
            self.assertEqual(rows[0]['Sleep'], "fair")
            self.assertEqual(rows[0]['Physical Activity'], "moderate")
            self.assertEqual(rows[0]['Triggers'], "Stress")
            self.assertEqual(rows[0]['Notes'], "TEST")
            self.assertEqual(rows[0]['Location'], "New York, NY")
            self.assertEqual(float(rows[0]['Latitude']), 40.7128)
            self.assertEqual(float(rows[0]['Longitude']), -74.0060)
            self.assertEqual(rows[0]['Timezone'], "America/New_York")

        # Check if the view_frame's update_entries method was called
        mock_view_frame.update_entries.assert_called_once()

if __name__ == '__main__':
    unittest.main()