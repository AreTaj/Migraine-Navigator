from fastapi import Query
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from api.models import MigraineEntry
from services.entry_service import EntryService
import pandas as pd
import os

from prediction.predict_future import get_prediction_for_date, clear_prediction_cache

router = APIRouter()

# Helper to get DB path (can be environment variable or config later)
def get_db_path():
    # Assuming standard project structure
    return os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'migraine_log.db')

@router.get("/entries", response_model=List[MigraineEntry])
def get_entries(start_date: str = Query(None, description="Filter start date (YYYY-MM-DD)"), 
                end_date: str = Query(None, description="Filter end date (YYYY-MM-DD)")):
    try:
        df = EntryService.get_entries_from_db(get_db_path(), start_date, end_date)
        # Convert DataFrame to list of dicts
        # Need to handle NaN/None values for Pydantic
        # Handle NaN values smartly
        # Pain Level should be 0 if missing
        if 'Pain Level' in df.columns:
            df['Pain Level'] = pd.to_numeric(df['Pain Level'], errors='coerce').fillna(0).astype(int)
            
        # Other columns can be empty strings
        df = df.fillna("")
        
        entries = []
        for _, row in df.iterrows():
            # Map 'Pain Level' (DB) to 'Pain_Level' (Model)
            entry_dict = row.to_dict()
            entry_dict['Pain_Level'] = entry_dict.pop('Pain Level', 0)
            entry_dict['Physical_Activity'] = entry_dict.pop('Physical Activity', "")

            # Fix for empty strings in float fields
            if entry_dict.get('Latitude') == '':
                entry_dict['Latitude'] = None
            if entry_dict.get('Longitude') == '':
                entry_dict['Longitude'] = None
                
            entries.append(entry_dict)
            
        return entries
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/entries")
def add_entry(entry: MigraineEntry):
    try:
        # Convert Pydantic model to dict for Service
        data = entry.model_dump()
        
        # Remap snake_case keys back to Title Case keys expected by Service/DB
        data['Pain Level'] = data.pop('Pain_Level')
        data['Physical Activity'] = data.pop('Physical_Activity')
        
        EntryService.add_entry(data, get_db_path())
        # Invalidate prediction cache so dashboard updates instantly
        clear_prediction_cache()
        return {"message": "Entry added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/entries/{entry_id}")
def delete_entry(entry_id: int):
    try:
        EntryService.delete_entry(entry_id, get_db_path())
        clear_prediction_cache()
        return {"message": f"Entry {entry_id} deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/entries/{entry_id}")
def update_entry(entry_id: int, entry: MigraineEntry):
    try:
        data = entry.model_dump()
        # Handle remapping
        data['Pain Level'] = data.pop('Pain_Level')
        data['Physical Activity'] = data.pop('Physical_Activity')
        if 'id' in data: del data['id'] # Don't update ID

        EntryService.update_entry(entry_id, data, get_db_path())
        clear_prediction_cache()
        return {"message": "Entry updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
