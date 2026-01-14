from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import List, Optional
from services.trigger_service import TriggerService

# Use centralized DB path resolution
# DB_PATH = get_db_path() # Removed global
from api.dependencies import get_db_path_dep

router = APIRouter()

class TriggerCreate(BaseModel):
    name: str
    category: Optional[str] = None

class TriggerUpdate(BaseModel):
    category: Optional[str] = None
    name: Optional[str] = None

class TriggerResponse(BaseModel):
    id: int
    name: str
    usage_count: int
    is_system_default: bool
    category: Optional[str] = None

@router.get("/triggers", response_model=List[TriggerResponse])
def get_triggers(db_path: str = Depends(get_db_path_dep)):
    try:
        return TriggerService.get_triggers(db_path)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/triggers", response_model=dict)
def add_trigger(trigger: TriggerCreate, db_path: str = Depends(get_db_path_dep)):
    try:
        new_id = TriggerService.add_trigger(trigger.name, db_path, trigger.category)
        return {"id": new_id, "name": trigger.name, "category": trigger.category, "message": "Trigger added successfully"}
    except ValueError as e:
        # Check if it's a conflict
        if "already exists" in str(e):
             raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.put("/triggers/{trigger_id}")
def update_trigger(trigger_id: int, update: TriggerUpdate, db_path: str = Depends(get_db_path_dep)):
    try:
        TriggerService.update_trigger(trigger_id, db_path, category=update.category, name=update.name)
        return {"message": "Trigger updated successfully"}
    except ValueError as e:
        if "already exists" in str(e):
             raise HTTPException(status_code=409, detail=str(e))
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.delete("/triggers/{trigger_id}")
def delete_trigger(trigger_id: int, db_path: str = Depends(get_db_path_dep)):
    try:
        TriggerService.delete_trigger(trigger_id, db_path)
        return {"message": "Trigger deleted successfully"}
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
