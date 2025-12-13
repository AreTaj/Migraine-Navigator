from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import sys
import os

# Add project root to path for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from prediction.predict_future import get_prediction_for_date

router = APIRouter(prefix="/prediction", tags=["prediction"])

@router.get("/future")
async def get_future_prediction(date: str = Query(None, description="Date in YYYY-MM-DD format. Defaults to tomorrow.")):
    """
    Get migraine risk prediction for a specific date.
    """
    if date is None:
        tomorrow = datetime.now() + timedelta(days=1)
        date = tomorrow.strftime("%Y-%m-%d")
    
    try:
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
        
        result = get_prediction_for_date(date)
        return result
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    except Exception as e:
        print(f"Prediction Error: {e}")
        # In prod, log this, don't expose detail
        raise HTTPException(status_code=500, detail=str(e))
