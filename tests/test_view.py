import unittest
from unittest.mock import patch, MagicMock
import os
import pandas as pd
import sys
from tkinter import Tk

# Add the top-level directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from view.view_frame import ViewFrame

class TestViewFrame(unittest.TestCase):
    def setUp(self):
        self.root = Tk()
        self.view_frame = ViewFrame(self.root, "test_migraine_log.csv")
        self.view_frame.pack()

        # Create a temporary CSV file
        with open("test_migraine_log.csv", 'w') as f:
            f.write("Date,Time,Pain Level,Medication,Dosage,Sleep,Physical Activity,Triggers,Notes,Location\n")

    def tearDown(self):
        self.root.destroy()
        if os.path.exists("test_migraine_log.csv"):
            os.remove("test_migraine_log.csv")

    @patch('pandas.read_csv')
    def test_load_entries_no_data(self, mock_read_csv):
        # Mock read_csv to return an empty DataFrame with the necessary columns
        mock_read_csv.return_value = pd.DataFrame(columns=[
            'Date', 'Time', 'Pain Level', 'Medication', 'Dosage', 'Sleep', 'Physical Activity', 'Triggers', 'Notes', 'Location'
        ])
        
        self.view_frame.load_entries()
        
        # Check if the Treeview is empty
        self.assertEqual(len(self.view_frame.entries_treeview.get_children()), 0)

    @patch('pandas.read_csv')
    def test_load_entries_with_data(self, mock_read_csv):
        # Mock read_csv to return a DataFrame with data
        mock_read_csv.return_value = pd.DataFrame({
            'Date': ['2023-10-10'],
            'Time': ['12:00'],
            'Pain Level': [5],
            'Medication': ['Ibuprofen'],
            'Dosage': ['200mg'],
            'Sleep': ['Fair'],
            'Physical Activity': ['Moderate'],
            'Triggers': ['Stress'],
            'Notes': ['Had a stressful day.'],
            'Location': ['New York, NY']
        })
        
        self.view_frame.load_entries()
        
        # Check if the Treeview has one entry
        self.assertEqual(len(self.view_frame.entries_treeview.get_children()), 1)

    @patch('pandas.read_csv')
    def test_update_entries(self, mock_read_csv):
        # Mock read_csv to return a DataFrame with data
        mock_read_csv.return_value = pd.DataFrame({
            'Date': ['2023-10-10'],
            'Time': ['12:00'],
            'Pain Level': [5],
            'Medication': ['Ibuprofen'],
            'Dosage': ['200mg'],
            'Sleep': ['Fair'],
            'Physical Activity': ['Moderate'],
            'Triggers': ['Stress'],
            'Notes': ['Had a stressful day.'],
            'Location': ['New York, NY']
        })
        
        self.view_frame.update_entries()
        
        # Check if the Treeview has one entry
        self.assertEqual(len(self.view_frame.entries_treeview.get_children()), 1)

if __name__ == '__main__':
    unittest.main()