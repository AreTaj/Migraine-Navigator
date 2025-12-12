from fastapi import APIRouter, HTTPException
from typing import List
from api.models import MigraineEntry
from services.entry_service import EntryService
import os

router = APIRouter()

# Helper to get DB path (can be environment variable or config later)
def get_db_path():
    # Assuming standard project structure
    return os.path.join(os.path.dirname(__file__), '..', '..', 'data', 'migraine_log.db')

@router.get("/entries", response_model=List[MigraineEntry])
def get_entries():
    try:
        df = EntryService.get_entries_from_db(get_db_path())
        # Convert DataFrame to list of dicts
        # Need to handle NaN/None values for Pydantic
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
        return {"message": "Entry added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
