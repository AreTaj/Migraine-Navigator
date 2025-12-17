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
DB_PATH = os.path.join(BASE_DIR, '..', 'data', 'migraine_log.db')

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
    Fetches weather from Open-Meteo for the specific date.
    Returns feature dictionary or None if failed.
    """
    try:
        # Open-Meteo API
        # Constraint: 'past_days' is relative to TODAY, not start_date.
        # To get yesterday's context (needed for Pressure Change calculation) for a future date, 
        # we must explicitly set start_date to target-1.
        
        start_dt = target_date - timedelta(days=1)
        start_str = start_dt.strftime('%Y-%m-%d')
        target_str = target_date.strftime('%Y-%m-%d')
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": start_str,
            "end_date": target_str,
            "hourly": "temperature_2m,relative_humidity_2m,surface_pressure,precipitation,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,sunshine_duration",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=5)
        # Check for error details before raising
        if response.status_code >= 400:
            print(f"Open-Meteo Error: {response.text}")
        response.raise_for_status()
        data = response.json()
        
        daily = data.get('daily', {})
        hourly = data.get('hourly', {})
        
        # With start_date = T-1 and end_date = T, we expect 2 days.
        # Index 0 = Yesterday (Context), Index 1 = Target.
        
        # Verify indices by time (Safest)
        times = hourly.get('time', [])
        target_hourly_idx = -1
        prev_hourly_idx = -1
        
        for i, t in enumerate(times):
            if t.startswith(target_str):
                # Found the start of target day (00:00)
                target_hourly_idx = i
            if t.startswith(start_str):
                prev_hourly_idx = i
                
        if target_hourly_idx == -1:
            return None
            
        # Target Day Hourly (24h)
        h_temps = hourly['temperature_2m'][target_hourly_idx : target_hourly_idx+24]
        h_hums = hourly['relative_humidity_2m'][target_hourly_idx : target_hourly_idx+24]
        h_pres = hourly['surface_pressure'][target_hourly_idx : target_hourly_idx+24]
        h_wspd = hourly['wind_speed_10m'][target_hourly_idx : target_hourly_idx+24]
        h_prcp = hourly['precipitation'][target_hourly_idx : target_hourly_idx+24]
        
        # Pressure Change (Target Avg - Previous Avg)
        pres_change = 0.0
        if prev_hourly_idx != -1:
            prev_pres_list = hourly['surface_pressure'][prev_hourly_idx : prev_hourly_idx+24]
            # Ensure we have full day
            if len(prev_pres_list) >= 24 and h_pres: 
                prev_avg_pres = sum(prev_pres_list) / len(prev_pres_list)
                curr_avg_pres = sum(h_pres) / len(h_pres)
                pres_change = curr_avg_pres - prev_avg_pres

        # Daily Aggregates
        # Find index for TARGET date in daily
        daily_times = daily.get('time', [])
        d_idx = -1
        for i, t in enumerate(daily_times):
            if t == target_str:
                d_idx = i
                break
        
        if d_idx == -1:
             # Fallback
            tmin = min(h_temps) if h_temps else 0
            tmax = max(h_temps) if h_temps else 0
            tsun = 0 
        else:
            tmin = daily['temperature_2m_min'][d_idx]
            tmax = daily['temperature_2m_max'][d_idx]
            tsun = (daily['sunshine_duration'][d_idx] or 0) / 60.0

        # Features Calculation
        tavg = sum(h_temps) / len(h_temps) if h_temps else 0
        pres = sum(h_pres) / len(h_pres) if h_pres else 1015.0
        humidity = sum(h_hums) / len(h_hums) if h_hums else 50.0
        wspd = sum(h_wspd) / len(h_wspd) if h_wspd else 0
        prcp = sum(h_prcp) if h_prcp else 0
        
        midday_humidity = h_hums[12] if len(h_hums) > 12 else humidity

        return {
            'id': -1,
            'tavg': tavg,
            'tmin': tmin,
            'tmax': tmax,
            'prcp': prcp,
            'wspd': wspd,
            'pres': pres,
            'tsun': tsun,
            'average_humidity': humidity,
            'pres_change': pres_change,
            'midday_humidity': midday_humidity
        }
        
    except Exception as e:
        print(f"Weather API Error (Open-Meteo): {e}")
        return None

def fetch_weekly_weather_forecast(start_date, lat, lon):
    """
    Fetches 7 days of weather starting from start_date in one API call.
    Returns a dict mapping date_str -> features.
    """
    try:
        # Request 7 days range
        # We also need previous day for the FIRST day's pressure change.
        # So we request start_date - 1 day to end_date + 6 days.
        
        real_start = start_date - timedelta(days=1)
        end_date = start_date + timedelta(days=6)
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": real_start.strftime('%Y-%m-%d'),
            "end_date": end_date.strftime('%Y-%m-%d'),
            "hourly": "temperature_2m,relative_humidity_2m,surface_pressure,precipitation,wind_speed_10m",
            "daily": "temperature_2m_max,temperature_2m_min,sunshine_duration",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get('hourly', {})
        daily = data.get('daily', {})
        
        daily_map = {} # date_str -> features
        
        # Loop for target days (0 to 6)
        for i in range(7):
            target = start_date + timedelta(days=i)
            target_str = target.strftime('%Y-%m-%d')
            prev_str = (target - timedelta(days=1)).strftime('%Y-%m-%d')
            
            # Find indices
            times = hourly.get('time', [])
            target_idx = -1
            prev_idx = -1
            for idx, t in enumerate(times):
                if t.startswith(target_str): target_idx = idx
                if t.startswith(prev_str): prev_idx = idx
            
            if target_idx == -1: continue 

            # Extract Hourly
            h_temps = hourly['temperature_2m'][target_idx : target_idx+24]
            h_hums = hourly['relative_humidity_2m'][target_idx : target_idx+24]
            h_pres = hourly['surface_pressure'][target_idx : target_idx+24]
            h_wspd = hourly['wind_speed_10m'][target_idx : target_idx+24]
            h_prcp = hourly['precipitation'][target_idx : target_idx+24]
            
            # Calc Pressure Change
            pres_change = 0.0
            if prev_idx != -1 and len(hourly['surface_pressure']) > prev_idx+24:
                prev_list = hourly['surface_pressure'][prev_idx : prev_idx+24]
                if prev_list and h_pres:
                    pres_change = (sum(h_pres)/len(h_pres)) - (sum(prev_list)/len(prev_list))

            # Daily
            d_times = daily.get('time', [])
            d_idx = -1
            for idx, t in enumerate(d_times):
                if t == target_str: d_idx = idx
            
            tsun = 0
            tmin = min(h_temps) if h_temps else 0
            tmax = max(h_temps) if h_temps else 0
            
            if d_idx != -1:
                tmin = daily['temperature_2m_min'][d_idx]
                tmax = daily['temperature_2m_max'][d_idx]
                tsun = (daily['sunshine_duration'][d_idx] or 0) / 60.0
            
            # Aggregate
            feat = {
                'id': -1,
                'tavg': sum(h_temps) / len(h_temps) if h_temps else 0,
                'tmin': tmin,
                'tmax': tmax,
                'prcp': sum(h_prcp) if h_prcp else 0,
                'wspd': sum(h_wspd) / len(h_wspd) if h_wspd else 0,
                'pres': sum(h_pres) / len(h_pres) if h_pres else 1015,
                'tsun': tsun,
                'average_humidity': sum(h_hums) / len(h_hums) if h_hums else 50,
                'pres_change': pres_change,
                'midday_humidity': h_hums[12] if len(h_hums) > 12 else 50
            }
            daily_map[target_str] = feat
            
        return daily_map

    except Exception as e:
        print(f"Batch Weather Error: {e}")
        return {}


def construct_features(target_date, history_df, manual_weather=None):
    """
    Builds a single-row DataFrame of features for the target_date.
    Uses history_df to calculate lags.
    If manual_weather is provided (dict), uses it instead of fetching.
    """
    features = {}
    
    # 1. Temporal Features (Cyclical Encoding)
    # We transform DayOfWeek (0-6) and Month (1-12) into Sine/Cosine pairs.
    # Why? because "Sunday" (6) is close to "Monday" (0).
    # Linear features (0,1,2...6) imply Monday(0) is far from Sunday(6).
    # Sin/Cos representation preserves this cyclical proximity for the model.
    features['DayOfWeek'] = target_date.dayofweek
    features['Month'] = target_date.month
    features['DayOfWeek_sin'] = np.sin(2 * np.pi * features['DayOfWeek'] / 7)
    features['DayOfWeek_cos'] = np.cos(2 * np.pi * features['DayOfWeek'] / 7)
    features['Month_sin'] = np.sin(2 * np.pi * features['Month'] / 12)
    features['Month_cos'] = np.cos(2 * np.pi * features['Month'] / 12)
    
    # 2. Weather (Live with Fallback)
    weather = None
    
    if manual_weather:
        weather = manual_weather
        if 'source' not in weather:
            weather['source'] = 'prefetched'
    else:
        lat, lon = get_latest_location_from_db()
        
        if lat and lon:
            try:
                weather = fetch_weather_forecast(target_date, lat, lon)
                if weather is None:
                    raise ValueError("API returned None")
                if 'source' not in weather:
                    weather['source'] = 'live'
            except Exception as e:
                print(f"Weather API unavailable ({e}). Attempting DB fallback...")
                # Fallback: Get most recent weather from DB
                try:
                    conn = sqlite3.connect(DB_PATH)
                    cursor = conn.cursor()
                    cursor.execute("""
                        SELECT tavg, tmin, tmax, pres, pres_change, prcp, wspd, tsun, average_humidity, midday_humidity, date
                        FROM weather_cache 
                        ORDER BY date DESC LIMIT 1
                    """)
                    row = cursor.fetchone()
                    conn.close()
                    
                    if row:
                        print(f"Using historical weather from {row[10]}")
                        weather = {
                            'id': -1,
                            'tavg': row[0] or 20.0,
                            'tmin': row[1] or 15.0,
                            'tmax': row[2] or 25.0,
                            'pres': row[3] or 1015.0,
                            'pres_change': row[4] or 0.0,
                            'prcp': row[5] or 0.0,
                            'wspd': row[6] or 10.0,
                            'tsun': row[7] or 600.0,
                            'average_humidity': row[8] or 50.0,
                            'midday_humidity': row[9] or 50.0,
                            'source': 'historical_fallback',
                            'source_date': row[10]
                        }
                    else:
                        raise ValueError("No historical weather in DB.")
                except Exception as db_err:
                    print(f"DB Fallback failed: {db_err}")
                    raise ValueError("Weather data unavailable (Live & DB failed).")

    if weather is None:
        raise ValueError("Weather data unavailable. Prediction cannot be made.")

    features.update(weather)
    features['tdiff'] = features['tmax'] - features['tmin']
    features['humid.*tavg'] = features['average_humidity'] * features['tavg']
    features['pres_change_lag1'] = 0.0 # Assume stability for future
    features['tavg_lag1'] = weather['tavg'] # Persistence
    
    # 3. Autoregressive (Lags) from History
    # We need the last N days of pain history relative to target_date
    
    # Create a quick lookup map
    # history_df has 'Date' (datetime) and 'Pain Level'
    pain_map = dict(zip(history_df['Date'].dt.date, history_df['Pain Level']))
    
    def get_pain_lag(days_ago):
        d = target_date.date() - timedelta(days=days_ago)
        return pain_map.get(d, 0.0)
    
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
    features['Sleep'] = 2.0 # Assume 'Fair' (Scale 1-3)
    features['Physical Activity'] = 1.5 # Assume 'Light-Moderate' (Scale 0-3)
    # features['midday_humidity'] is already in weather dict
    
    # Adding source info to features dict for retrieval
    # (DataFrame constructor usually ignores extra keys if we just pass dict, 
    # but we will return the dict separately too)
    
    return pd.DataFrame([features]), features

_prediction_cache = {}

def clear_prediction_cache():
    """
    Clears the in-memory prediction cache. 
    Call this whenever underlying data (entries or settings) changes.
    """
    global _prediction_cache
    _prediction_cache.clear()
    print("Prediction cache cleared.")

def get_prediction_for_date(target_date_str, weather_override=None):
    """
    Main API entry point.
    """
    # 1. Check Cache (1 Hour TTL)
    # We cache predictions to avoid spamming the Open-Meteo API and to make the UI instant.
    if target_date_str in _prediction_cache:
        entry = _prediction_cache[target_date_str]
        age = datetime.datetime.now() - entry["timestamp"]
        if age < timedelta(hours=1):
            print(f"Using cached prediction for {target_date_str}")
            return entry["result"]

    target_date = pd.to_datetime(target_date_str)
    
    # Load history (Lags)
    # This fetches recent user logs to calculate "Recent Pain" features.
    history = get_recent_history()
    
    # Construct features
    X, meta = construct_features(target_date, history, manual_weather=weather_override)
    
    # Load Models
        # Load Models
    clf, reg = load_models()
    
    # Reorder columns to match training data
    # This prevents "Feature names must be in the same order" error
    if hasattr(clf, 'feature_names_in_'):
        X = X[clf.feature_names_in_]
    
    # 2. Predict Probability (Classifier)
    # [No Pain, Pain]
    probs = clf.predict_proba(X)[0]
    prob_migraine = probs[1]
    
    # Apply Threshold Adjustment (Optional, if we want to tune sensitivity manually)
    # prob_migraine = prob_migraine * 1.5 # Example adjustment
    
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
        "predicted_pain": round(pred_pain, 1) if prob_migraine > 0.2 else 0.0,
        "source": meta.get('source', 'live'),
        "source_date": meta.get('source_date', None)
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
