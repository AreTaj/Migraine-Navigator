import unittest
from unittest.mock import patch, MagicMock
import os
import pandas as pd
import sys
import matplotlib.pyplot as plt
from tkinter import Tk

# Add the top-level directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from analysis.analysis_frame import AnalysisFrame

class TestAnalysisFrame(unittest.TestCase):
    def setUp(self):
        self.root = Tk()
        self.analysis_frame = AnalysisFrame(self.root, "test_migraine_log.csv")
        self.analysis_frame.pack()

        # Create a temporary CSV file
        with open("test_migraine_log.csv", 'w') as f:
            f.write("Date,Pain Level,Medication\n")

    def tearDown(self):
        self.root.destroy()
        if os.path.exists("test_migraine_log.csv"):
            os.remove("test_migraine_log.csv")

    @patch('pandas.read_csv')
    def test_perform_analysis_no_data(self, mock_read_csv):
        # Mock read_csv to return an empty DataFrame
        mock_read_csv.return_value = pd.DataFrame()
        
        self.analysis_frame.perform_analysis()
        
        self.assertEqual(self.analysis_frame.analysis_content.cget("text"), "No data found in the CSV file.")

    @patch('pandas.read_csv')
    def test_perform_analysis_invalid_date_format(self, mock_read_csv):
        # Mock read_csv to return a DataFrame with invalid date format
        mock_read_csv.return_value = pd.DataFrame({
            'Date': ['invalid_date'],
            'Pain Level': [5]
        })
        
        self.analysis_frame.perform_analysis()
        
        self.assertEqual(self.analysis_frame.analysis_content.cget("text"), "Invalid date format in data. Please use YYYY-MM-DD.")

    @patch('pandas.read_csv')
    def test_perform_analysis_valid_data(self, mock_read_csv):
        # Mock read_csv to return a valid DataFrame
        mock_read_csv.return_value = pd.DataFrame({
            'Date': ['2023-10-10'],
            'Pain Level': [5],
            'Medication': ['Ibuprofen']
        })
        
        self.analysis_frame.perform_analysis()
        
        self.assertIsNotNone(self.analysis_frame.analysis_result)

    def test_plot_migraines_yearly(self):
        # Create a sample DataFrame
        data = pd.Series([1, 2, 3], index=[2021, 2022, 2023])
        
        fig, ax = plt.subplots()
        self.analysis_frame.plot_migraines_yearly(ax, data)
        
        # Check if the plot has the correct title
        self.assertEqual(ax.get_title(), "Migraine Days per Year")
        
        # Check if the plot has the correct labels
        self.assertEqual(ax.get_ylabel(), "Count")
        self.assertEqual(ax.get_xticks().tolist(), [2021, 2022, 2023])

if __name__ == '__main__':
    unittest.main()