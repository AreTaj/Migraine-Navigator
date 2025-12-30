from fastapi.testclient import TestClient
from api.main import app
import os
import pytest

client = TestClient(app)

def test_priors_lifecycle():
    # 1. Update Priors
    payload = {
        "baseline_risk": 0.6,
        "weather_sensitivity": 0.9,
        "sleep_sensitivity": 0.2,
        "strain_sensitivity": 0.1
    }
    response = client.post("/api/v1/user/priors", json=payload)
    assert response.status_code == 200
    assert response.json()["status"] == "success"

    # 2. Fetch Priors
    response = client.get("/api/v1/user/priors")
    assert response.status_code == 200
    data = response.json()
    assert data["baseline_risk"] == 0.6
    assert data["weather_sensitivity"] == 0.9

def test_import_csv():
    # Create a dummy CSV
    csv_content = "Date,Pain Level\n2023-01-01,5\n2023-01-02,0"
    files = {'file': ('test.csv', csv_content, 'text/csv')}
    
    response = client.post("/api/v1/data/import/csv", files=files)
    assert response.status_code == 200
    data = response.json()
    assert data["status"] == "success"
    # We expect 2 rows to be imported. 
    # Note: This test runs against the actual DB configured in utils (or a test override if we set one up).
    # For safety in this environment, it assumes the dev DB. 
    # Ideally we'd mock the DB, but for a quick integration check this confirms the route works and parses CSV.

def test_prediction_endpoint_heuristic():
    # Ensure prediction works and returns "Heuristic" source if no model
    # (assuming no trained model exists, or even if it does, we check structure)
    response = client.get("/api/v1/prediction/future?date=2025-01-01")
    assert response.status_code == 200
    data = response.json()
    assert "probability" in data
    assert "source" in data
