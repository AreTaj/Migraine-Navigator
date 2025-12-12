import unittest
import pandas as pd
from unittest.mock import patch, MagicMock
import sys
import os

# Ensure services module is visible
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.analysis_service import AnalysisService

class TestAnalysisService(unittest.TestCase):

    @patch('services.entry_service.EntryService.get_entries_from_db')
    def test_get_analysis_data_empty(self, mock_get_entries):
        # Setup: Empty DataFrame
        mock_get_entries.return_value = pd.DataFrame()

        # Execute
        result = AnalysisService.get_analysis_data("test.db")

        # Assert: Should return None or empty structure (based on implementation)
        self.assertIsNone(result)

    @patch('services.entry_service.EntryService.get_entries_from_db')
    def test_get_analysis_data_valid(self, mock_get_entries):
        # Setup: Valid Data
        data = pd.DataFrame({
            'Date': ['2023-01-01', '2023-01-02'],
            'Pain Level': [5, 8],
            'Medication': ['Tylenol', ''], # Test empty med normalization
            'Physical Activity': ['None', 'Light']
        })
        mock_get_entries.return_value = data

        # Execute
        result = AnalysisService.get_analysis_data("test.db")

        # Assert Structure
        self.assertIsNotNone(result)
        self.assertIn("avg_pain", result)
        self.assertIn("max_pain", result)
        self.assertIn("medication_counts", result)

        # Assert Logic
        self.assertEqual(result['avg_pain'], 6.5)
        self.assertEqual(result['max_pain'], 8)
        
        # Check "No Medication" normalization
        meds = result['medication_counts']
        self.assertIn("No Medication", meds)
        self.assertEqual(meds['No Medication'], 1) 
        self.assertIn("Tylenol", meds)

    @patch('services.entry_service.EntryService.get_entries_from_db')
    def test_pain_filtering(self, mock_get_entries):
        # Setup: Mix of Pain > 0 and Pain = 0
        data = pd.DataFrame({
            'Date': ['2023-01-01', '2023-01-02'],
            'Pain Level': [5, 0], # One migraine, one non-migraine
            'Medication': ['A', 'B']
        })
        mock_get_entries.return_value = data

        result = AnalysisService.get_analysis_data("test.db")
        
        # Avg/Max should only consider Pain > 0
        self.assertEqual(result['avg_pain'], 5.0) 
        # Medication counts logic: My code currently filters for Pain > 0 for med counts too? 
        # Let's verify expectations: "Filter for entries with Pain > 0 to identify Migraine Episodes"
        
        meds = result['medication_counts']
        self.assertIn("A", meds)
        self.assertNotIn("B", meds)

if __name__ == '__main__':
    unittest.main()
