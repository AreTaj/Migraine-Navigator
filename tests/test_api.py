import unittest
from fastapi.testclient import TestClient
from api.main import app
import os
from unittest.mock import patch
import pandas as pd

client = TestClient(app)

class TestAPI(unittest.TestCase):

    @patch('api.routes.entries.get_db_path')
    @patch('api.routes.analysis.get_db_path')
    def test_read_root(self, mock_analysis_db, mock_entries_db):
        response = client.get("/")
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Welcome to Migraine Navigator API"})

    @patch('api.routes.entries.get_db_path')
    @patch('api.routes.analysis.get_db_path')
    def test_create_and_read_entry(self, mock_analysis_db, mock_entries_db):
        test_db = "test_api.db"
        mock_entries_db.return_value = test_db
        mock_analysis_db.return_value = test_db
        
        # Clean up
        if os.path.exists(test_db):
            os.remove(test_db)

        # 1. Create Entry
        entry_data = {
            "Date": "2023-10-10",
            "Time": "12:00",
            "Pain_Level": 5,
            "Medication": "Advil",
            "Dosage": "200mg",
            "Sleep": "Good",
            "Physical_Activity": "Moderate", 
            "Triggers": "Stress",
            "Notes": "API Test",
            "Location": "Home",
            "Latitude": 10.0,
            "Longitude": 20.0
        }
        
        response = client.post("/api/v1/entries", json=entry_data)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {"message": "Entry added successfully"})

        # 2. Read Entries
        response = client.get("/api/v1/entries")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertEqual(data[0]['Notes'], "API Test")
        self.assertEqual(data[0]['Pain_Level'], 5)
        
        # 3. Validation Error Check (Missing required field)
        invalid_data = {"Date": "2023-10-10"} # Missing Time, Pain_Level etc.
        response = client.post("/api/v1/entries", json=invalid_data)
        self.assertEqual(response.status_code, 422) # Unprocessable Entity

        # Clean up
        if os.path.exists(test_db):
            os.remove(test_db)

    @patch('api.routes.entries.get_db_path')
    @patch('api.routes.analysis.get_db_path')
    def test_analysis_endpoint(self, mock_analysis_db, mock_entries_db):
        test_db = "test_api_analysis.db"
        mock_entries_db.return_value = test_db
        mock_analysis_db.return_value = test_db
        
        if os.path.exists(test_db):
            os.remove(test_db)

        # Insert data first via API
        entry_data = {
            "Date": "2023-10-10",
            "Time": "12:00",
            "Pain_Level": 5,
            "Medication": "Advil",
            "Dosage": "200mg",
            "Sleep": "Good",
            "Physical_Activity": "Moderate"
        }
        client.post("/api/v1/entries", json=entry_data)
        
        # Test Analysis
        response = client.get("/api/v1/analysis/summary")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        
        # Check structure
        self.assertIn("yearly_counts", data)
        self.assertIn("medication_counts", data)
        self.assertIn("Advil", data['medication_counts'])
        
        if os.path.exists(test_db):
            os.remove(test_db)

    @patch('api.routes.entries.get_db_path')
    @patch('api.routes.analysis.get_db_path')
    @patch('services.entry_service.EntryService.get_entries_from_db')
    def test_read_entry_with_empty_float_fields(self, mock_get_entries, mock_analysis_db, mock_entries_db):
        """
        Regression test: Ensure API handles empty strings in float fields (Latitude/Longitude)
        gracefully by converting them to None, avoiding 500 errors.
        """
        # Mock returning a List of Dicts (not DataFrame) as EntryService logic actually does
        mock_get_entries.return_value = [{
            "Date": "2023-10-10",
            "Time": "12:00",
            "Pain Level": 5,
            "Medication": "",
            "Dosage": "",
            "Sleep": "Good",
            "Physical Activity": "Moderate",
            "Triggers": "",
            "Notes": "Empty Lat/Lon",
            "Location": "",
            "Latitude": "",    # The problematic empty string
            "Longitude": ""    # The problematic empty string
        }]

        response = client.get("/api/v1/entries")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertEqual(len(data), 1)
        self.assertIsNone(data[0]['Latitude'])
        self.assertIsNone(data[0]['Longitude'])

    @patch('api.routes.user.get_db_path')
    def test_user_priors(self, mock_user_db):
        test_db = "test_api_priors.db"
        mock_user_db.return_value = test_db
        
        if os.path.exists(test_db):
            os.remove(test_db)
            
        # 1. Get Default Priors
        response = client.get("/api/v1/user/priors")
        self.assertEqual(response.status_code, 200)
        data = response.json()
        self.assertFalse(data['force_heuristic_mode'])
        
        # 2. Update Priors (Enable Force Mode)
        new_priors = data
        new_priors['force_heuristic_mode'] = True
        new_priors['weather_sensitivity'] = 0.9
        
        response = client.post("/api/v1/user/priors", json=new_priors)
        self.assertEqual(response.status_code, 200)
        
        # 3. Verify Persistence
        response = client.get("/api/v1/user/priors")
        data = response.json()
        self.assertTrue(data['force_heuristic_mode'])
        self.assertEqual(data['weather_sensitivity'], 0.9)
        
        if os.path.exists(test_db):
            os.remove(test_db)

if __name__ == '__main__':
    unittest.main()


