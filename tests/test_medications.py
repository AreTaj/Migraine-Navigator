import pytest
import sqlite3
import os
import json
from fastapi.testclient import TestClient
from api.main import app
from api.models import Medication
from services.entry_service import EntryService
from services.medication_service import MedicationService

TEST_DB = "test_migraine.db"

@pytest.fixture
def db_path():
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)
    yield TEST_DB
    if os.path.exists(TEST_DB):
        os.remove(TEST_DB)

from unittest.mock import patch

@pytest.fixture
def client(db_path):
    # Since the app uses a hardcoded get_db_path function internally in routes,
    # we need to mock THAT function, not use dependency_overrides.
    # We also need to initializing the DB tables.
    
    # 1. Init DB
    conn = sqlite3.connect(db_path)
    MedicationService._create_table_if_not_exists(conn)
    EntryService._create_table_if_not_exists(conn)
    conn.close()

    # 2. Mock the path
    # We need to patch where it is USED.
    with patch('api.routes.medications.get_db_path', return_value=db_path), \
         patch('api.routes.entries.get_db_path', return_value=db_path): 
        with TestClient(app) as c:
            yield c

@pytest.fixture
def setup_db(client):
    # Just ensures client is running
    pass

def test_create_medication(setup_db, client):
    new_med = {
        "name": "Botox",
        "display_name": "Botox Injection",
        "default_dosage": "155 Units",
        "frequency": "periodic",
        "period_days": 90
    }
    response = client.post("/api/v1/medications", json=new_med)
    assert response.status_code == 200
    data = response.json()
    assert data["name"] == "Botox"
    assert data["frequency"] == "periodic"
    assert data["period_days"] == 90
    assert "id" in data

def test_get_medications(setup_db, client):
    client.post("/api/v1/medications", json={"name": "Advil", "display_name": "Advil", "frequency": "as_needed"})
    client.post("/api/v1/medications", json={"name": "Topamax", "display_name": "Topamax", "frequency": "daily"})
    
    response = client.get("/api/v1/medications")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 2
    # Assuming the order might not be guaranteed, check by name
    advil = next((m for m in data if m["name"] == "Advil"), None)
    topamax = next((m for m in data if m["name"] == "Topamax"), None)

    assert advil is not None
    assert advil["frequency"] == "as_needed"
    assert advil["period_days"] is None # as_needed should not have period_days

    assert topamax is not None
    assert topamax["frequency"] == "daily"
    assert topamax["period_days"] is None # daily should not have period_days

def test_entry_with_meds_json(db_path):
    # Add entry with new structure
    entry_data = {
        "Date": "2023-01-01",
        "Time": "12:00",
        "Pain Level": 5,
        "Medications": [{"name": "Advil", "dosage": "200mg"}],
        "Sleep": "Good",
        "Physical Activity": "None"
    }
    
    # Validation should pass and data inserted
    EntryService.add_entry(entry_data, db_path)
    
    # Read back raw to check storage
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    c.execute("SELECT Medications FROM migraine_log")
    raw_json = c.fetchone()[0]
    conn.close()
    
    assert raw_json is not None
    loaded = json.loads(raw_json)
    assert isinstance(loaded, list)
    assert loaded[0]['name'] == "Advil"

    # Read back via service
    df = EntryService.get_entries_from_db(db_path)
    assert df.iloc[0]['Medications'][0]['name'] == "Advil"


def test_migration(db_path):
    # 1. Setup DB with legacy schema and data manually
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Create table WITHOUT Medications column first (simulating old state)
    c.execute("""
        CREATE TABLE migraine_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date TEXT,
            Time TEXT,
            "Pain Level" INTEGER,
            Medication TEXT,
            Dosage TEXT,
            Sleep TEXT,
            "Physical Activity" TEXT,
            Triggers TEXT,
            Notes TEXT,
            Location TEXT,
            Timezone TEXT,
            Latitude REAL,
            Longitude REAL
        )
    """)
    # Insert legacy data
    c.execute("INSERT INTO migraine_log (Date, Time, Medication, Dosage) VALUES (?, ?, ?, ?)", 
              ("2023-01-01", "12:00", "OldMed", "50mg"))
    # Insert empty medication entry
    c.execute("INSERT INTO migraine_log (Date, Time, Medication, Dosage) VALUES (?, ?, ?, ?)", 
              ("2023-01-02", "13:00", "", ""))
    conn.commit()
    conn.close()

    # 2. Trigger Migration by calling _create_table_if_not_exists (or adding a new entry which calls it)
    # This should detect missing column, add it, and run migration
    conn = sqlite3.connect(db_path)
    EntryService._create_table_if_not_exists(conn)
    conn.close()

    # 3. Verify
    conn = sqlite3.connect(db_path)
    c = conn.cursor()
    # Check if column exists
    c.execute("PRAGMA table_info(migraine_log)")
    cols = [info[1] for info in c.fetchall()]
    assert "Medications" in cols

    # Check data migration
    c.execute("SELECT Medications, Medication FROM migraine_log ORDER BY Date")
    rows = c.fetchall()
    conn.close()

    # Row 1: OldMed should be migrated
    json_val = rows[0][0]
    assert json_val is not None
    data = json.loads(json_val)
    assert data[0]['name'] == "OldMed"
    assert data[0]['dosage'] == "50mg"

    # Row 2: Empty med should NOT be migrated (should remain None or empty list depending on logic, our logic ignores empty strings)
    # Our migration query: WHERE Medications IS NULL AND Medication != ''
    # So row 2 should still have Medications as NULL (since we didn't touch it)
    assert rows[1][0] is None
