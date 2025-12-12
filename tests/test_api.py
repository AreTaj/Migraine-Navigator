from fastapi.testclient import TestClient
from api.main import app
import os
import pytest
from unittest.mock import patch
import pandas as pd

client = TestClient(app)

# We mock get_db_path to use a test database
@patch('api.routes.entries.get_db_path')
@patch('api.routes.analysis.get_db_path')
def test_read_root(mock_analysis_db, mock_entries_db):
    response = client.get("/")
    assert response.status_code == 200
    assert response.json() == {"message": "Welcome to Migraine Navigator API"}

@patch('api.routes.entries.get_db_path')
@patch('api.routes.analysis.get_db_path')
def test_create_and_read_entry(mock_analysis_db, mock_entries_db):
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
    assert response.status_code == 200
    assert response.json() == {"message": "Entry added successfully"}

    # 2. Read Entries
    response = client.get("/api/v1/entries")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['Notes'] == "API Test"
    assert data[0]['Pain_Level'] == 5
    
    # 3. Validation Error Check (Missing required field)
    invalid_data = {"Date": "2023-10-10"} # Missing Time, Pain_Level etc.
    response = client.post("/api/v1/entries", json=invalid_data)
    assert response.status_code == 422 # Unprocessable Entity

    # Clean up
    if os.path.exists(test_db):
        os.remove(test_db)

@patch('api.routes.entries.get_db_path')
@patch('api.routes.analysis.get_db_path')
def test_analysis_endpoint(mock_analysis_db, mock_entries_db):
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
    assert response.status_code == 200
    data = response.json()
    
    # Check structure
    assert "yearly_counts" in data
    assert "medication_counts" in data
    assert "Advil" in data['medication_counts']
    
    if os.path.exists(test_db):
        os.remove(test_db)

@patch('api.routes.entries.get_db_path')
@patch('api.routes.analysis.get_db_path')
@patch('services.entry_service.EntryService.get_entries_from_db')
def test_read_entry_with_empty_float_fields(mock_get_entries, mock_analysis_db, mock_entries_db):
    """
    Regression test: Ensure API handles empty strings in float fields (Latitude/Longitude)
    gracefully by converting them to None, avoiding 500 errors.
    """
    # Mock returning a DataFrame with empty strings for numeric fields
    mock_get_entries.return_value = pd.DataFrame([{
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
    }])

    response = client.get("/api/v1/entries")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]['Latitude'] is None
    assert data[0]['Longitude'] is None
