from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import sys
import os

# from forecasting.predict_future import get_prediction_for_date, fetch_weekly_weather_forecast, get_latest_location_from_db
# Lazy loaded inside functions

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
        
        from forecasting.predict_future import get_prediction_for_date
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
        
        # 1. Use Recursive Forecasting Logic to ensure future lags are populated
        from forecasting.predict_future import get_weekly_forecast_recursive
        
        forecasts = get_weekly_forecast_recursive(start_date)
            
        return forecasts
    except Exception as e:
        print(f"Forecast Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
