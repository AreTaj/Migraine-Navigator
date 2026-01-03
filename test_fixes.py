import sys
import os
import datetime

# Ensure we can import from project root
sys.path.insert(0, os.getcwd())

try:
    from forecasting.inference import get_hourly_forecast, get_weekly_forecast
    print("Dependencies loaded.")
except ImportError as e:
    print(f"Error loading dependencies: {e}")
    sys.exit(1)

print("\n--- TEST 1: Hourly Forecast (simulating API call with date=None) ---")
try:
    # This crashed previously with 'NoneType has no strftime'
    result = get_hourly_forecast(None)
    
    if len(result) > 0:
        print(f"SUCCESS: Returned {len(result)} hourly slots.")
        print(f"Sample: {result[0]}")
    else:
        print("WARNING: Returned empty list (might still be failing silently or network error).")

except Exception as e:
    print(f"FAIL: Crashed with error: {e}")
    sys.exit(1)

print("\n--- TEST 2: Weekly Forecast (simulating API call w/o args) --")
try:
    result_week = get_weekly_forecast()
    if len(result_week) == 7:
         print(f"SUCCESS: Returned {len(result_week)} daily forecasts.")
         print(f"Sample: {result_week[0]}")
    else:
         print(f"WARNING: Unexpected length {len(result_week)}")
except Exception as e:
    print(f"FAIL: Crashed with error: {e}")
    sys.exit(1)
