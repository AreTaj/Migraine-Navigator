from fastapi import APIRouter, HTTPException
from typing import List
from api.models import Medication
from services.medication_service import MedicationService
import os

router = APIRouter()

def get_db_path():
    return os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'migraine_log.db')

@router.get("/medications", response_model=List[Medication])
def get_medications():
    try:
        meds = MedicationService.get_medications(get_db_path())
        return meds
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/medications")
def add_medication(med: Medication):
    try:
        new_id = MedicationService.add_medication(med.model_dump(exclude_unset=True), get_db_path())
        # Return full object with ID
        response_data = med.model_dump()
        response_data["id"] = new_id
        # Ensure defaults are propagated if missing from input but handled in DB/Service? 
        # Ideally we refetch, but for now just merging input + default.
        if "frequency" not in response_data: response_data["frequency"] = "as_needed"
        return response_data
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/medications/{med_id}")
def update_medication(med_id: int, med: Medication):
    try:
        MedicationService.update_medication(med_id, med.model_dump(exclude_unset=True), get_db_path())
        return {"message": "Medication updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/medications/{med_id}")
def delete_medication(med_id: int):
    try:
        MedicationService.delete_medication(med_id, get_db_path())
        return {"message": "Medication deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/medications/import")
def import_medications_from_history():
    try:
        count = MedicationService.scan_and_import_history(get_db_path())
        return {"message": f"Successfully imported {count} new medications from history", "count": count}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
