from fastapi import APIRouter, HTTPException, Query
from datetime import datetime, timedelta
import sys
import os

# from forecasting.inference import get_prediction_for_date, fetch_weekly_weather_forecast, get_latest_location_from_db
# Lazy loaded inside functions

router = APIRouter(prefix="/prediction", tags=["prediction"])

import logging
import os
from api.utils import get_data_dir

# Setup logger
logger = logging.getLogger("prediction_route")
handler = logging.FileHandler(os.path.join(get_data_dir(), "api_debug.log"))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also log to Console
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)

@router.get("/future")
def get_future_prediction(date: str = Query(None, description="Date in YYYY-MM-DD format. Defaults to tomorrow.")):
    """
    Get migraine risk prediction for a specific date.
    """
    if date is None:
        tomorrow = datetime.now() + timedelta(days=1)
        date = tomorrow.strftime("%Y-%m-%d")
    
    try:
        logger.info(f"GET /prediction/future request for {date}")
        # Validate date format
        datetime.strptime(date, "%Y-%m-%d")
        
        logger.debug("Importing inference...")
        from forecasting.inference import get_prediction_for_date
        logger.debug("Calling get_prediction_for_date...")
        
        result = get_prediction_for_date(date)
        logger.info("Prediction successful")
        return result
    except ValueError:
        logger.warning(f"Invalid date format: {date}")
        raise HTTPException(status_code=400, detail="Invalid date format. Use YYYY-MM-DD.")
    except Exception as e:
        logger.error(f"Prediction Error: {str(e)}", exc_info=True)

        raise HTTPException(status_code=500, detail=str(e))

@router.get("/forecast")
def get_weekly_forecast():
    """
    Get migraine risk prediction for the next 7 days (Starting Tomorrow).
    """
    try:
        start_date = datetime.now() + timedelta(days=1)
        forecasts = []
        
        # 1. Use Recursive Forecasting Logic to ensure future lags are populated
        from forecasting.inference import get_weekly_forecast_recursive
        
        forecasts = get_weekly_forecast_recursive(start_date)
            
        return forecasts
    except Exception as e:
        logger.error(f"Forecast Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/hourly")
def get_hourly_prediction(date: str = Query(None, description="Start date/time in YYYY-MM-DD HH:MM format (optional)"), hours: int = 24):
    """
    Get hourly risk forecast for the next 24 (or N) hours.
    """
    try:
        from forecasting.inference import get_hourly_forecast
        
        # If date is not provided, use current time
        # The underlying function handles None/empty string by using now()
        
        forecast = get_hourly_forecast(date)
        return forecast
        
    except Exception as e:
        logger.error(f"Hourly Forecast Error: {e}", exc_info=True)
        raise HTTPException(status_code=500, detail=str(e))

