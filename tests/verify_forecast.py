import asyncio
import sys
import os
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.getcwd())

from forecasting.inference import get_prediction_for_date
from services.weather_service import WeatherService

async def verify_forecast():
    print("Verifying 7-Day Forecast logic...")
    start_date = datetime.now() + timedelta(days=1)
    
    print("1. Testing Batch Weather Fetch...")
    # lat, lon for LA
    weekly_weather = WeatherService.fetch_weekly(start_date, 34.05, -118.25)
    print(f"Batch fetch returned {len(weekly_weather)} days.")
    
    if len(weekly_weather) == 0:
        print("FAILURE: Batch fetch failed.")
        return

    print("Sample Day 1:", list(weekly_weather.values())[0])
    
    print("\n2. Testing Prediction Loop...")
    for i in range(3):
        target_date = start_date + timedelta(days=i)
        d_str = target_date.strftime("%Y-%m-%d")
        
        # Test valid override
        if d_str in weekly_weather:
            pred = get_prediction_for_date(d_str, weather_override=weekly_weather[d_str])
            print(f"SUCCESS (Batch): {d_str} -> Risk: {pred.get('probability')}, Source: {pred.get('source')}")
        else:
            print(f"MISSING WEATHER for {d_str}")

if __name__ == "__main__":
    asyncio.run(verify_forecast())
