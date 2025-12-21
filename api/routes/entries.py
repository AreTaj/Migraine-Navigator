from fastapi import Query
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from api.models import MigraineEntry
from services.entry_service import EntryService
import os

from forecasting.predict_future import get_prediction_for_date, clear_prediction_cache

router = APIRouter()

from api.utils import get_db_path
@router.get("/entries", response_model=List[MigraineEntry])
def get_entries(start_date: str = Query(None, description="Filter start date (YYYY-MM-DD)"), 
                end_date: str = Query(None, description="Filter end date (YYYY-MM-DD)")):
    try:
        entries_data = EntryService.get_entries_from_db(get_db_path(), start_date, end_date)
        
        processed_entries = []
        for entry in entries_data:
            # Handle missing numeric values (Pain Level default 0)
            try:
                if entry.get('Pain Level') is not None:
                    entry['Pain Level'] = int(float(entry['Pain Level']))
                else:
                    entry['Pain Level'] = 0
            except (ValueError, TypeError):
                entry['Pain Level'] = 0
            
            # Use 'entry' directly since it's already a dict
            # Map 'Pain Level' (DB) to 'Pain_Level' (Model)
            # Create a new dict for the model to avoid mutating the original if reused
            model_entry = entry.copy()
            
            model_entry['Pain_Level'] = model_entry.pop('Pain Level', 0)
            model_entry['Physical_Activity'] = model_entry.pop('Physical Activity', "")
            
            # Map legacy column names if they exist and aren't None, else default to None or ""
            # The DB returns keys as they are in the columns (e.g. "Physical Activity")
            
            # Fix for empty strings in float fields
            if model_entry.get('Latitude') == '':
                model_entry['Latitude'] = None
            if model_entry.get('Longitude') == '':
                model_entry['Longitude'] = None
                
            # Replace None strings with empty strings for text fields if needed, 
            # though Pydantic usually handles Optional[str] fine.
            # But the original code did df.fillna(""), so we replicate that behavior 
            # for string fields primarily.
            for k, v in model_entry.items():
                if v is None and k not in ['Latitude', 'Longitude', 'Pain_Level']:
                    model_entry[k] = ""
                
            processed_entries.append(model_entry)
            
        return processed_entries
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
