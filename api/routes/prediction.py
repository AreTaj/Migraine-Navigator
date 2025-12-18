from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import sys
import os

# Add project root to path for imports
BASE_DIR = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if BASE_DIR not in sys.path:
    sys.path.append(BASE_DIR)

from prediction.predict_future import get_prediction_for_date, fetch_weekly_weather_forecast, get_latest_location_from_db

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
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forecast")
async def get_weekly_forecast():
    """
    Get migraine risk prediction for the next 7 days (Starting Tomorrow).
    """
    try:
        start_date = datetime.now() + timedelta(days=1)
        forecasts = []
        
        # 1. Fetch Weather Batch (Optimize speed)
        lat, lon = get_latest_location_from_db() 
        if not lat:
             lat, lon = 34.05, -118.25 # Default: Los Angeles
             
        weather_map = fetch_weekly_weather_forecast(start_date, lat, lon)
        
        for i in range(7):
            target_date = start_date + timedelta(days=i)
            date_str = target_date.strftime("%Y-%m-%d")
            
            # Use pre-fetched weather if available
            day_weather = weather_map.get(date_str)
            
            pred = get_prediction_for_date(date_str, weather_override=day_weather)
            
            forecasts.append({
                "date": date_str,
                "risk_probability": pred.get("probability", 0),
                "risk_level": pred.get("risk_level", "Unknown"),
                "source": pred.get("source", "unknown")
            })
            
        return forecasts
    except Exception as e:
        print(f"Forecast Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
