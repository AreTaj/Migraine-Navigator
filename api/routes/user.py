from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel
from typing import Optional
import sqlite3
from ..utils import get_db_path

router = APIRouter(prefix="/user", tags=["user"])

class UserPriors(BaseModel):
    baseline_risk: float
    weather_sensitivity: float
    sleep_sensitivity: float
    strain_sensitivity: float
    temp_unit: str = 'C'

# DB Helper (Quick and dirty for now, should use a proper dependency)
def get_db():
    return get_db_path()

@router.get("/priors", response_model=UserPriors)
async def get_user_priors():
    """
    Get the current user's sensitivity priors.
    """
    db_path = get_db()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()
        
        # Check if table exists
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        if not cursor.fetchone():
            # Create if not exists (Lazy migration)
            cursor.execute("""
                CREATE TABLE user_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
            conn.commit()
            
        # Fetch values
        cursor.execute("SELECT key, value FROM user_settings WHERE key IN ('baseline_risk', 'weather_sensitivity', 'sleep_sensitivity', 'strain_sensitivity', 'temp_unit')")
        rows = dict(cursor.fetchall())
        conn.close()
        
        return UserPriors(
            baseline_risk=float(rows.get('baseline_risk', 0.1)),
            weather_sensitivity=float(rows.get('weather_sensitivity', 0.5)),
            sleep_sensitivity=float(rows.get('sleep_sensitivity', 0.5)),
            strain_sensitivity=float(rows.get('strain_sensitivity', 0.5)),
            temp_unit=rows.get('temp_unit', 'C')
        )
        
    except Exception as e:
        print(f"Error fetching priors: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/priors")
async def update_user_priors(priors: UserPriors):
    """
    Update the user's sensitivity priors.
    """
    db_path = get_db()
    try:
        conn = sqlite3.connect(db_path)
        cursor = conn.cursor()

        # Ensure table exists (Lazy migration)
        cursor.execute("SELECT name FROM sqlite_master WHERE type='table' AND name='user_settings'")
        if not cursor.fetchone():
            cursor.execute("""
                CREATE TABLE user_settings (
                    key TEXT PRIMARY KEY,
                    value TEXT
                )
            """)
        
        # Upsert values
        data = [
            ('baseline_risk', str(priors.baseline_risk)),
            ('weather_sensitivity', str(priors.weather_sensitivity)),
            ('sleep_sensitivity', str(priors.sleep_sensitivity)),
            ('strain_sensitivity', str(priors.strain_sensitivity)),
            ('temp_unit', priors.temp_unit)
        ]
        
        cursor.executemany("INSERT OR REPLACE INTO user_settings (key, value) VALUES (?, ?)", data)
        conn.commit()
        conn.close()
        
        # Invalidate prediction cache if we update settings
        try:
             from forecasting.inference import clear_prediction_cache
             clear_prediction_cache()
        except ImportError:
             pass # Might happen if module not loaded yet
             
        return {"status": "success", "priors": priors}
        
    except Exception as e:
        print(f"Error updating priors: {e}")
        raise HTTPException(status_code=500, detail=str(e))
