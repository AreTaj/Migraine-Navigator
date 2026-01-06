import os
import sqlite3
from services.medication_service import MedicationService
from services.entry_service import EntryService
from services.trigger_service import TriggerService

DB_PATH = "test_usage.db"

def setup():
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)

def test_usage_tracking():
    print("--- 1. Creating Meds & Triggers ---")
    # Add meds (A: Ibuprofen, B: Tylenol, C: Excedrin)
    MedicationService.add_medication({"name": "Ibuprofen"}, DB_PATH) # Will be used 2x
    MedicationService.add_medication({"name": "Tylenol"}, DB_PATH)   # Will be used 0x
    MedicationService.add_medication({"name": "Excedrin"}, DB_PATH)  # Will be used 3x
    
    # Add triggers
    TriggerService.add_trigger("Stress", DB_PATH)
    
    print("--- 2. Creating Entries ---")
    # Entry 1: Excedrin, Stress
    EntryService.add_entry({
        "Date": "2023-01-01", "Time": "12:00", "Pain Level": 5,
        "Medications": [{"name": "Excedrin", "dosage": "2"}],
        "Triggers": "Stress"
    }, DB_PATH)
    
    # Entry 2: Excedrin, Ibuprofen
    EntryService.add_entry({
        "Date": "2023-01-02", "Time": "12:00", "Pain Level": 5,
        "Medications": [{"name": "Excedrin", "dosage": "2"}, {"name": "Ibuprofen", "dosage": "200mg"}],
        "Triggers": ""
    }, DB_PATH)

    # Entry 3: Excedrin, Ibuprofen
    EntryService.add_entry({
        "Date": "2023-01-03", "Time": "12:00", "Pain Level": 5,
        "Medications": [{"name": "Excedrin", "dosage": "2"}, {"name": "Ibuprofen", "dosage": "200mg"}],
        "Triggers": ""
    }, DB_PATH)
    
    print("--- 3. Verifying Counts & Sort Order ---")
    meds = MedicationService.get_medications(DB_PATH)
    
    # Debug Print
    for m in meds:
        print(f"Med: {m['name']}, Usage: {m['usage_count']}")
        
    # Validation Logic
    # Order should be: Excedrin (3), Ibuprofen (2), Tylenol (0)
    assert meds[0]['name'] == 'Excedrin', f"Expected Excedrin first, got {meds[0]['name']}"
    assert meds[0]['usage_count'] == 3, f"Expected Excedrin count 3, got {meds[0]['usage_count']}"
    
    assert meds[1]['name'] == 'Ibuprofen', f"Expected Ibuprofen second, got {meds[1]['name']}"
    assert meds[1]['usage_count'] == 2, f"Expected Ibuprofen count 2, got {meds[1]['usage_count']}"
    
    assert meds[2]['name'] == 'Tylenol', f"Expected Tylenol third, got {meds[2]['name']}"
    assert meds[2]['usage_count'] == 0, f"Expected Tylenol count 0, got {meds[2]['usage_count']}"
    
    print("SUCCESS: Medication sorting works!")

    # Verify Triggers
    triggers = TriggerService.get_triggers(DB_PATH)
    t = triggers[0]
    print(f"Trigger: {t['name']}, Usage: {t['usage_count']}")
    
    assert t['name'] == 'Stress'
    assert t['usage_count'] == 1
    print("SUCCESS: Trigger tracking works!")

if __name__ == "__main__":
    setup()
    try:
        test_usage_tracking()
    finally:
        if os.path.exists(DB_PATH):
            os.remove(DB_PATH)
