from fastapi import Query
from fastapi import APIRouter, HTTPException
from typing import List, Optional
from api.models import MigraineEntry
from services.entry_service import EntryService
import os

# Prediction functions are lazy-loaded within routes to speed up backend startup
# and avoid triggering ML sub-dependencies (like matplotlib) until needed.

router = APIRouter()

from api.utils import get_db_path
import logging
import os
from api.utils import get_data_dir

# Setup logger
logger = logging.getLogger("entries_route")
handler = logging.FileHandler(os.path.join(get_data_dir(), "api_debug.log"))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

@router.get("/entries", response_model=List[MigraineEntry])
def get_entries(start_date: str = Query(None, description="Filter start date (YYYY-MM-DD)"), 
                end_date: str = Query(None, description="Filter end date (YYYY-MM-DD)"),
                limit: int = Query(None, description="Limit number of entries")):
    try:
        logger.info(f"GET /entries request. Limit: {limit}, Start: {start_date}, End: {end_date}")
        entries_data = EntryService.get_entries_from_db(get_db_path(), start_date, end_date)
        logger.info(f"Retrieved {len(entries_data)} entries from DB")
        
        # Apply limit manually if service doesn't support it yet
        if limit and len(entries_data) > limit:
             entries_data = entries_data[:limit]
        
        processed_entries = []
        for i, entry in enumerate(entries_data):
            # logger.debug(f"Processing entry {i}: {entry.get('id')}") # Verbose
            
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
            model_entry = entry.copy()
            
            model_entry['Pain_Level'] = model_entry.pop('Pain Level', 0)
            model_entry['Physical_Activity'] = model_entry.pop('Physical Activity', "")
            
            # --- ROBUST SANITIZATION (Fix for Issue #758) ---
            # 1. Fix Medications: Must be a list of objects. 
            # If DB has garbage (e.g. int/str), force empty list to prevent Pydantic 500.
            if not isinstance(model_entry.get('Medications'), list):
                # logger.warning(f"Sanitizing invalid Medications: {model_entry.get('Medications')}")
                model_entry['Medications'] = []
            
            # 2. Fix Geo Fields: Must be float or None. 
            # If DB has garbage (e.g. '[]', empty string), force None.
            for geo in ['Latitude', 'Longitude']:
                val = model_entry.get(geo)
                if val == '' or val == '[]' or val is None:
                    model_entry[geo] = None
                else:
                    try:
                        model_entry[geo] = float(val)
                    except (ValueError, TypeError):
                        # logger.warning(f"Sanitizing invalid {geo}: {val}")
                        model_entry[geo] = None

            # 3. Fix general text fields
            for k, v in model_entry.items():
                if v is None and k not in ['Latitude', 'Longitude', 'Pain_Level', 'Medications']:
                    model_entry[k] = ""
                
            processed_entries.append(model_entry)
            
        logger.info(f"Successfully processed {len(processed_entries)} entries")
        return processed_entries
    except Exception as e:
        logger.error(f"Error in get_entries: {str(e)}", exc_info=True)
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
        try:
            from forecasting.inference import clear_prediction_cache
            clear_prediction_cache()
        except ImportError:
            pass
        return {"message": "Entry added successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/entries/{entry_id}")
def delete_entry(entry_id: int):
    try:
        EntryService.delete_entry(entry_id, get_db_path())
        try:
            from forecasting.inference import clear_prediction_cache
            clear_prediction_cache()
        except ImportError:
            pass
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
        try:
            from forecasting.inference import clear_prediction_cache
            clear_prediction_cache()
        except ImportError:
            pass
        return {"message": "Entry updated successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
