import pytest
import sqlite3
import pandas as pd
import json
import os
from prediction.train_model import train_and_evaluate
from prediction.data_processing import load_migraine_log_from_db

TEST_DB_PATH = "test_prediction_safety.db"

@pytest.fixture
def setup_safety_db():
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)
    
    conn = sqlite3.connect(TEST_DB_PATH)
    c = conn.cursor()
    # Create schema matching production
    c.execute("""
        CREATE TABLE migraine_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date TEXT,
            Time TEXT,
            "Pain Level" INTEGER,
            Medication TEXT,
            Dosage TEXT,
            Medications TEXT,
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
    
    # Insert Mixed Data Types
    
    # 1. Standard Old Entry (Migraine)
    c.execute("INSERT INTO migraine_log (Date, Time, `Pain Level`, Medication, Dosage, Sleep, `Physical Activity`) VALUES (?, ?, ?, ?, ?, ?, ?)",
             ("2023-01-01", "10:00", 7, "Advil", "200mg", "Poor", "None"))
             
    # 2. New Format Entry (Migraine with JSON Meds)
    meds_json = json.dumps([{"name": "Ubrelvy", "dosage": "50mg"}])
    c.execute("INSERT INTO migraine_log (Date, Time, `Pain Level`, Medications, Sleep, `Physical Activity`) VALUES (?, ?, ?, ?, ?, ?)",
             ("2023-01-02", "12:00", 8, meds_json, "Fair", "Light"))
             
    # 3. Healthy Check-in (Pain=0, Daily Meds)
    daily_json = json.dumps([{"name": "Topamax", "dosage": "50mg"}])
    c.execute("INSERT INTO migraine_log (Date, Time, `Pain Level`, Medications, Sleep, `Physical Activity`) VALUES (?, ?, ?, ?, ?, ?)",
             ("2023-01-03", "12:00", 0, daily_json, "Good", "Moderate"))
             
    # 4. Retroactive "No-Meds" Check-in (Pain=0, Empty Meds)
    c.execute("INSERT INTO migraine_log (Date, Time, `Pain Level`, Medications, Sleep, `Physical Activity`) VALUES (?, ?, ?, ?, ?, ?)",
             ("2023-01-04", "12:00", 0, "[]", "Good", "Heavy"))

    # 5. Some more data to ensure enough for split (mimicking tiny dataset)
    for i in range(10):
        c.execute("INSERT INTO migraine_log (Date, Time, `Pain Level`, Sleep, `Physical Activity`) VALUES (?, ?, ?, ?, ?)",
                 (f"2023-02-{10+i}", "10:00", (i % 2) * 5, "Good", "Moderate"))

    conn.commit()
    conn.close()
    
    yield TEST_DB_PATH
    
    if os.path.exists(TEST_DB_PATH):
        os.remove(TEST_DB_PATH)

def test_training_pipeline_safety(setup_safety_db):
    """
    Crucial Test: Run the ACTUAL training pipeline function on the mixed database.
    If this crashes, the new feature broke the core product.
    """
    print(f"\nTesting Prediction Pipeline on: {setup_safety_db}")
    
    # 1. Verify Data Loading
    df = load_migraine_log_from_db(setup_safety_db)
    assert len(df) >= 14
    # Check that 'Medications' column exists but didn't break loading
    assert 'Medications' in df.columns
    
    # 2. Run Training
    # We expect it to handle Pain=0 entries (usually filtered or specific logic)
    # The key is that it shouldn't throw an error due to the new column types.
    try:
        model, accuracy, report = train_and_evaluate(setup_safety_db)
        print(f"\nTraining Successful. Accuracy: {accuracy}")
        assert model is not None
        assert accuracy >= 0 # Just checking it ran, accuracy might be garbage on fake data
    except Exception as e:
        pytest.fail(f"Training pipeline CRASHED with new data format: {e}")
