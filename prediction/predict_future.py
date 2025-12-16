import pandas as pd
import numpy as np
import os
import joblib
import sqlite3
import datetime
from datetime import timedelta

import sys
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import data processing helpers
from prediction.data_processing import load_migraine_log_from_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, '..', 'models')
MODEL_CLF_PATH = os.path.join(MODEL_DIR, 'best_model_clf.pkl')
MODEL_REG_PATH = os.path.join(MODEL_DIR, 'best_model_reg.pkl')

_clf_model = None
_reg_model = None

def load_models():
    global _clf_model, _reg_model
    if _clf_model is None:
        if not os.path.exists(MODEL_CLF_PATH):
            raise FileNotFoundError("Model files not found. Please train the model first.")
        _clf_model = joblib.load(MODEL_CLF_PATH)
        _reg_model = joblib.load(MODEL_REG_PATH)
    return _clf_model, _reg_model

def get_recent_history(db_path=None, days=60):
    """
    Fetches the last N days of data from the DB to calculate lags.
    """
    df = load_migraine_log_from_db(db_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Ensure numeric types
    for col in ['Pain Level', 'Sleep', 'Physical Activity']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Sort and take recent
    df = df.sort_values('Date').tail(days).reset_index(drop=True)
    return df

import requests

def get_latest_location_from_db(db_path=None):
    """
    Fetches the most recent location (Lat/Lon) from the DB.
    """
    try:
        df = load_migraine_log_from_db(db_path)
        # Drop rows with missing location
        df = df.dropna(subset=['Latitude', 'Longitude'])
        if df.empty:
            return None, None
        
        # Sort by Date descending
        df['Date'] = pd.to_datetime(df['Date'])
        latest = df.sort_values('Date', ascending=False).iloc[0]
        return latest['Latitude'], latest['Longitude']
    except Exception as e:
        print(f"Error fetching location: {e}")
        return None, None

def fetch_weather_forecast(target_date, lat, lon):
    """
    Fetches weather from wttr.in for the specific date.
    Returns feature dictionary or None if failed.
    """
    try:
        # wttr.in returns 3 days: today, tomorrow, day after.
        # We need to find our target date in that list.
        url = f"https://wttr.in/{lat},{lon}?format=j1"
        response = requests.get(url, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        target_str = target_date.strftime('%Y-%m-%d')
        
        weather_days = data.get('weather', [])
        found_day = None
        for day in weather_days:
            if day.get('date') == target_str:
                found_day = day
                break
        
        if not found_day:
            return None # Date not in forecast range
            
        # Parse fields
        # wttr.in gives hourly data, we can aggregate
        hourly = found_day.get('hourly', [])
        
        # Averages from hourly
        temps = [float(h['tempC']) for h in hourly]
        pressures = [float(h['pressure']) for h in hourly]
        humidities = [float(h['humidity']) for h in hourly]
        
        # Features
        tavg = float(found_day.get('avgtempC', 0))
        tmin = float(found_day.get('mintempC', 0))
        tmax = float(found_day.get('maxtempC', 0))
        tsun = float(found_day.get('sunHour', 0)) * 60.0 # Convert hours to minutes
        pres = sum(pressures) / len(pressures) if pressures else 1015.0
        humidity = sum(humidities) / len(humidities) if humidities else 50.0
        
        return {
            'id': -1,
            'tavg': tavg,
            'tmin': tmin,
            'tmax': tmax,
            'prcp': 0.0, # tough to get total from hourly without summing precipMM
            'wspd': 10.0, # default/avg
            'pres': pres,
            'tsun': tsun,
            'average_humidity': humidity,
            'pres_change': 0.0, # Assumption
            'midday_humidity': humidity # approximate
        }
        
    except Exception as e:
        print(f"Weather API Error: {e}")
        return None

def mock_weather_forecast(target_date):
    """
    Returns plausible weather data for a future date.
    Fallback if API fails.
    """
    # Simple seasonal logic
    month = target_date.month
    
    # Northern hemisphere temp proxy
    if 4 <= month <= 9:
        tavg = 20.0
    else:
        tavg = 10.0
        
    return {
        'id': -1, # Dummy ID to appease model if it trained on 'id'
        'tavg': tavg,
        'tmin': tavg - 5,
        'tmax': tavg + 5,
        'prcp': 0.0,
        'wspd': 10.0,
        'pres': 1015.0,
        'tsun': 600.0,
        'average_humidity': 60.0,
        'pres_change': 0.0, # Stable pressure assumed
        'midday_humidity': 60.0 
    }

def construct_features(target_date, history_df):
    """
    Builds a single-row DataFrame of features for the target_date.
    Uses history_df to calculate lags.
    """
    features = {}
    
    # 1. Temporal
    features['DayOfWeek'] = target_date.dayofweek
    features['Month'] = target_date.month
    features['DayOfWeek_sin'] = np.sin(2 * np.pi * features['DayOfWeek'] / 7)
    features['DayOfWeek_cos'] = np.cos(2 * np.pi * features['DayOfWeek'] / 7)
    features['Month_sin'] = np.sin(2 * np.pi * features['Month'] / 12)
    features['Month_cos'] = np.cos(2 * np.pi * features['Month'] / 12)
    
    # 2. Weather (Live or Mock)
    weather = None
    lat, lon = get_latest_location_from_db()
    if lat and lon:
        weather = fetch_weather_forecast(target_date, lat, lon)
        if weather:
            print(f"Using live weather for {target_date.date()} in {lat},{lon}")
    
    if weather is None:
        print("Using seasonal weather fallback.")
        weather = mock_weather_forecast(target_date)
        
    features.update(weather)
    features['tdiff'] = features['tmax'] - features['tmin']
    features['humid.*tavg'] = features['average_humidity'] * features['tavg']
    features['pres_change_lag1'] = 0.0 # Assume stability
    features['tavg_lag1'] = weather['tavg'] # Persistence
    
    # 3. Autoregressive (Lags)
    # We need to find the Pain Level N days ago relative to TARGET date.
    # history_df has 'Date' and 'Pain Level'
    
    # Map Date -> Pain
    pain_map = dict(zip(history_df['Date'].dt.date, history_df['Pain Level']))
    
    def get_pain_lag(days_ago):
        d = target_date.date() - timedelta(days=days_ago)
        return pain_map.get(d, 0.0) # Default to 0 if missing
    
    features['Pain_Lag_1'] = get_pain_lag(1)
    features['Pain_Lag_2'] = get_pain_lag(2)
    features['Pain_Lag_3'] = get_pain_lag(3)
    features['Pain_Lag_7'] = get_pain_lag(7)
    
    # Rolling Means
    # We need a series ending at target_date - 1 day
    # Get last 30 days values
    last_30_vals = []
    for i in range(1, 31):
        last_30_vals.append(get_pain_lag(i))
    
    features['Pain_Rolling_Mean_3'] = np.mean(last_30_vals[:3])
    features['Pain_Rolling_Mean_7'] = np.mean(last_30_vals[:7])
    features['Pain_Rolling_Mean_30'] = np.mean(last_30_vals)
    
    # Add dummies for valid missing columns
    features['Sleep'] = 7.0 # Assume average sleep
    features['Physical Activity'] = 30.0 # Assume average activity
    # features['midday_humidity'] is already in weather dict
    
    return pd.DataFrame([features])

_prediction_cache = {}

def get_prediction_for_date(target_date_str):
    """
    Main API entry point.
    """
    # 1. Check Cache (1 Hour TTL)
    if target_date_str in _prediction_cache:
        entry = _prediction_cache[target_date_str]
        age = datetime.datetime.now() - entry["timestamp"]
        if age < timedelta(hours=1):
            print(f"Using cached prediction for {target_date_str}")
            return entry["result"]

    target_date = pd.to_datetime(target_date_str)
    
    # Load history
    history = get_recent_history()
    
    # Construct features
    X = construct_features(target_date, history)
    
    # Load Models
    clf, reg = load_models()
    
    # Reorder columns to match training data
    # This prevents "Feature names must be in the same order" error
    if hasattr(clf, 'feature_names_in_'):
        X = X[clf.feature_names_in_]
    
    # Predict Probability
    # clf.classes_ is likely [0, 1], so we take index 1
    probs = clf.predict_proba(X)[0]
    prob_migraine = probs[1]
    
    # Predict Severity
    pred_log_pain = reg.predict(X)[0]
    pred_pain = np.expm1(pred_log_pain) # Inverse log
    pred_pain = max(0, min(10, pred_pain)) # Clip 0-10
    
    # Risk Level
    # Based on our tuned threshold of 0.20
    if prob_migraine > 0.6:
        risk = "High"
    elif prob_migraine > 0.2:
        risk = "Moderate"
    else:
        risk = "Low"
        
    result = {
        "date": target_date_str,
        "probability": round(prob_migraine * 100, 1),
        "risk_level": risk,
        "predicted_pain": round(pred_pain, 1) if prob_migraine > 0.2 else 0.0
    }

    # Updating Cache
    _prediction_cache[target_date_str] = {
        "timestamp": datetime.datetime.now(),
        "result": result
    }
        
    return result

if __name__ == "__main__":
    # Test for tomorrow
    tomorrow = (datetime.datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Predicting for {tomorrow}...")
    result = get_prediction_for_date(tomorrow)
    print(result)
