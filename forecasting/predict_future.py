import os
import sqlite3
import datetime
from datetime import timedelta
from typing import TYPE_CHECKING
import sys
import logging

# Lazy loaded inside functions but imported here for typing if needed
if TYPE_CHECKING:
    import pandas as pd
    import numpy as np
    import joblib

# from forecasting.predict_future import get_prediction_for_date, fetch_weekly_weather_forecast, get_latest_location_from_db
from .data_processing import load_migraine_log_from_db

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, '..', 'models')
MODEL_CLF_PATH = os.path.join(MODEL_DIR, 'best_model_clf.pkl')
MODEL_REG_PATH = os.path.join(MODEL_DIR, 'best_model_reg.pkl')
from api.utils import get_db_path

DB_PATH = get_db_path()

_clf_model = None
_reg_model = None

def load_models():
    global _clf_model, _reg_model
    if _clf_model is None:
        import joblib
        import pandas as pd
        if not os.path.exists(MODEL_CLF_PATH):
            raise FileNotFoundError("Model files not found")
        # Logger is defined at module level in previous chunk, but to be safe we can use global or getLogger
        l = logging.getLogger("predict_future")
        l.debug("Loading CLF model...")
        _clf_model = joblib.load(MODEL_CLF_PATH)
        l.debug("Loading REG model...")
        _reg_model = joblib.load(MODEL_REG_PATH)
    return _clf_model, _reg_model

def get_recent_history(db_path=None, days=60):
    """
    Fetches the last N days of data from the DB to calculate lags.
    """
    import pandas as pd
    
    df = load_migraine_log_from_db(db_path)
    df['Date'] = pd.to_datetime(df['Date'])
    
    # Ensure numeric types
    for col in ['Pain Level', 'Sleep', 'Physical Activity']:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')

    # Sort and take recent
    df = df.sort_values('Date').tail(days).reset_index(drop=True)
    df = df.sort_values('Date').tail(days).reset_index(drop=True)
    return df

def get_circadian_priors(db_path=None):
    """
    Analyzes all historical migraine start times to build a 24-hour probability distribution.
    Returns a list of 24 floats (0.0-1.0) representing risk probability for each hour of the day.
    """
    import pandas as pd
    import numpy as np
    
    df = load_migraine_log_from_db(db_path)
    if df.empty:
        return [0.1] * 24 # Flat prior if no data
        
    # Filter for entries with Pain > 0
    pain_df = df[pd.to_numeric(df['Pain Level'], errors='coerce') > 0].copy()
    if pain_df.empty:
        return [0.1] * 24
        
    # Extract Hour
    # Check format of 'Time'. Assuming HH:MM or similar.
    # We need to robustly parse 'Time'.
    valid_hours = []
    for t_str in pain_df['Time']:
        try:
            if pd.isna(t_str): continue
            # Handle "10:30" or "10:30:00"
            h = int(str(t_str).split(':')[0])
            valid_hours.append(h)
        except:
            continue
            
    if not valid_hours:
        return [0.1] * 24
        
    # Build Histogram
    counts = np.bincount(valid_hours, minlength=24)
    total = len(valid_hours)
    
    # Raw Probability
    probs = counts / total
    
    # Smoothing (Gaussian-like rolling window)
    # Because "10:00" is close to "11:00", risk should bleed over.
    smoothed_probs = np.zeros(24)
    for i in range(24):
        # Weighted sum of i-1, i, i+1 (wrapping around)
        prev_i = (i - 1) % 24
        next_i = (i + 1) % 24
        
        # Weights: Center=0.6, Neighbors=0.2
        p = (probs[prev_i]*0.2) + (probs[i]*0.6) + (probs[next_i]*0.2)
        smoothed_probs[i] = p
        
    # Normalize to a 0-1 "Risk Factor"
    # Identify the "Peak Hour" probability to scale others relative to it?
    # Or just use the raw probability scaled up? 
    # Let's scale so that the Peak Hour = 0.8 (High Risk)
    max_p = np.max(smoothed_probs)
    if max_p > 0:
        smoothed_probs = (smoothed_probs / max_p) * 0.8
    else:
        smoothed_probs = np.full(24, 0.1)
        
    return smoothed_probs


import requests

def get_latest_location_from_db(db_path=None):
    """
    Fetches the most recent location (Lat/Lon) from the DB.
    """
    import pandas as pd
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
        logger.error(f"Error fetching location: {e}")
        return None, None

def fetch_weather_forecast(target_date, lat, lon):
    """
    Fetches weather from Open-Meteo for the specific date.
    Returns feature dictionary or None if failed.
    """
    try:
        # Open-Meteo API: Request weather for target date.
        # We need start_date = target - 1 day to calculate pressure change context from "yesterday".
        
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
            logger.error(f"Open-Meteo Error: {response.text}")
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
        logger.error(f"Weather API Error (Open-Meteo): {e}")
        return None

def fetch_hourly_weather(start_datetime, lat, lon, hours=24):
    """
    Fetches raw hourly weather for [start_datetime, start_datetime + hours].
    Returns list of dicts.
    """
    # ... reused logic from fetch_weather_forecast but returning list ...
    try:
        start_str = start_datetime.strftime('%Y-%m-%d')
        end_dt = start_datetime + timedelta(hours=hours) # Ideally +1 day to cover overlap
        end_str = (end_dt + timedelta(days=1)).strftime('%Y-%m-%d')
        
        # We need T-3 context for pressure change.
        # So request start_date - 1 day
        req_start = (start_datetime - timedelta(days=1)).strftime('%Y-%m-%d')
        
        url = "https://api.open-meteo.com/v1/forecast"
        params = {
            "latitude": lat,
            "longitude": lon,
            "start_date": req_start,
            "end_date": end_str,
            "hourly": "temperature_2m,relative_humidity_2m,surface_pressure,precipitation,wind_speed_10m",
            "timezone": "auto"
        }
        
        response = requests.get(url, params=params, timeout=5)
        response.raise_for_status()
        data = response.json()
        
        hourly = data.get('hourly', {})
        times = hourly.get('time', [])
        
        result_hours = []
        
        # Find start index
        # Time format is usually ISO: "2025-12-31T10:00"
        # We want to start exactly at the hour of start_datetime
        target_iso_start = start_datetime.strftime('%Y-%m-%dT%H:00')
        
        start_idx = -1
        for i, t in enumerate(times):
            if t >= target_iso_start:
                start_idx = i
                break
                
        if start_idx == -1: return []
        
        # Collect 'hours' amount of data points
        for i in range(start_idx, min(start_idx + hours, len(times))):
            # Calculate 3h Pressure Change
            # P_t - P_{t-3}
            # We need to ensure i-3 is valid
            pres_change_3h = 0.0
            if i >= 3:
                curr_p = hourly['surface_pressure'][i] or 1015
                prev_p = hourly['surface_pressure'][i-3] or 1015
                pres_change_3h = curr_p - prev_p
            
            w_dict = {
                'time': times[i],
                'temp': hourly['temperature_2m'][i],
                'humidity': hourly['relative_humidity_2m'][i],
                'pressure': hourly['surface_pressure'][i],
                'pressure_change_3h': pres_change_3h,
                'prcp': hourly['precipitation'][i],
                'wind': hourly['wind_speed_10m'][i]
            }
            result_hours.append(w_dict)
            
        return result_hours
        
    except Exception as e:
        logger.error(f"Hourly Weather Error: {e}")
        return []


def fetch_weekly_weather_forecast(start_date, lat, lon):
    import requests
    import pandas as pd
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
                'midday_humidity': h_hums[12] if len(h_hums) > 12 else 50,
                'Latitude': lat,
                'Longitude': lon
            }
            daily_map[target_str] = feat
            
        return daily_map

    except Exception as e:
        logger.error(f"Batch Weather Error: {e}")
        return {}


def construct_features(target_date, history_df, manual_weather=None):
    import pandas as pd
    import numpy as np
    """
    Builds a single-row DataFrame of features for the target_date.
    Uses history_df to calculate lags.
    If manual_weather is provided (dict), uses it instead of fetching.
    """
    features = {}
    
    # 1. Temporal Features (Cyclical Encoding)
    # Transform DayOfWeek (0-6) and Month (1-12) into Sin/Cos pairs to preserve cyclical proximity 
    # (e.g., Sunday (6) is close to Monday (0)).
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
                
                # Add location to weather dict (Model expects these)
                weather['Latitude'] = lat
                weather['Longitude'] = lon
                
                if 'source' not in weather:
                    weather['source'] = 'live'
            except Exception as e:
                logger.warning(f"Weather API unavailable ({e}). Attempting DB fallback...")
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
                        logger.info(f"Using historical weather from {row[10]}")
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
                            'source_date': row[10],
                            'Latitude': lat if lat else 0.0,
                            'Longitude': lon if lon else 0.0
                        }
                    else:
                        raise ValueError("No historical weather in DB.")
                except Exception as db_err:
                    logger.error(f"DB Fallback failed: {db_err}")
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
    logger.info("Prediction cache cleared.")

# ... imports at top ...
from api.utils import get_data_dir

# Setup logger for this module
logger = logging.getLogger("predict_future")
handler = logging.FileHandler(os.path.join(get_data_dir(), "api_debug.log"))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Also log to Console (stdout) so granular info is visible
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)

def get_prediction_for_date(target_date_str, weather_override=None):
    logger.debug(f"Starting prediction for {target_date_str}")
    
    try:
        t0 = datetime.datetime.now()
        import pandas as pd
        import numpy as np
        t1 = datetime.datetime.now()
        logger.debug(f"Pandas/Numpy imported successfully in {(t1-t0).total_seconds():.2f}s")
    except ImportError as e:
        logger.error(f"Failed to import pandas/numpy: {e}")
        raise e

    """
    Main API entry point.
    """
    # 1. Check Cache (1 Hour TTL)
    if target_date_str in _prediction_cache:
        # ... existing cache check ...
        pass # Skipping cache logic display for brevity in replacement

    target_date = pd.to_datetime(target_date_str)
    
    # Load history (Lags)
    logger.debug("Fetching recent history...")
    t2 = datetime.datetime.now()
    history = get_recent_history()
    t3 = datetime.datetime.now()
    logger.debug(f"History fetched. Rows: {len(history)} in {(t3-t2).total_seconds():.2f}s")
    
    # Construct features
    logger.debug("Constructing features...")
    X, meta = construct_features(target_date, history, manual_weather=weather_override)
    t4 = datetime.datetime.now()
    logger.debug(f"Features constructed in {(t4-t3).total_seconds():.2f}s. Source: {meta.get('source')}")
    
    # Load Models
    try:
        logger.debug("Loading models...")
        clf, reg = load_models()
        t5 = datetime.datetime.now()
        logger.debug(f"Models loaded in {(t5-t4).total_seconds():.2f}s")
        # Check if we have enough history for ML (e.g., > 30 days of data)
        # For now, we trust load_models raising FileNotFoundError if not trained.
        
        # Reorder columns to match training data
        if hasattr(clf, 'feature_names_in_'):
            X = X[clf.feature_names_in_]
        
        # 2. Predict Probability (Classifier)
        probs = clf.predict_proba(X)[0]
        prob_migraine = probs[1]
        
        # Predict Severity
        pred_log_pain = reg.predict(X)[0]
        pred_pain = np.expm1(pred_log_pain) 
        pred_pain = max(0, min(10, pred_pain))
        
        # Risk Level
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
            "source": meta.get('source', 'live') + " (ML)",
            "source_date": meta.get('source_date', None)
        }

    except (FileNotFoundError, Exception) as e:
        logger.warning(f"ML Model unavailable ({e}). Switching to Heuristic Engine.")
        
        # Hybrid Fallback: Heuristic Modle
        from .heuristic_predictor import HeuristicPredictor
        
        # Connect to DB to fetch User Priors
        user_priors = {}
        try:
            conn = sqlite3.connect(DB_PATH)
            conn.row_factory = sqlite3.Row
            cursor = conn.cursor()
            cursor.execute("SELECT key, value FROM user_settings")
            rows = cursor.fetchall()
            for row in rows:
                try:
                    user_priors[row['key']] = float(row['value'])
                except ValueError:
                    pass
            conn.close()
        except Exception as db_err:
            logger.warning(f"Failed to load user priors: {db_err}")

        # Initialize with User Priors (or defaults if DB fetch failed)
        predictor = HeuristicPredictor(user_priors)
        
        # Map features to Heuristic inputs
        # We extract 'Pain_Lag_1' from X if available (pandas DF) or manually from history
        yesterday_pain = 0.0
        if isinstance(X, pd.DataFrame) and 'Pain_Lag_1' in X.columns:
            yesterday_pain = float(X.iloc[0]['Pain_Lag_1'])
        
        heuristic_weather = {
            'pressure_change': meta.get('pres_change', 0.0),
            'prcp': meta.get('prcp', 0.0),
            'average_humidity': meta.get('average_humidity', 50.0)
        }
        
        # Heuristic Prediction with full context
        pred = predictor.predict(
            weather_data=heuristic_weather,
            yesterday_pain=yesterday_pain,
            sleep_data=0.0, # TODO: Wire up actual sleep debt tracking
            strain_data=0.0 # TODO: Wire up actual strain tracking
        )
        
        result = {
            "date": target_date_str,
            "probability": round(pred['probability'] * 100, 1),
            "risk_level": pred['risk_level'],
            "predicted_pain": 0.0, # Heuristic doesn't predict pain magnitude yet
            "source": meta.get('source', 'live') + " (Heuristic)",
            "source_date": meta.get('source_date', None),
            "components": pred.get('components', {})
        }

    # Updating Cache
    _prediction_cache[target_date_str] = {
        "timestamp": datetime.datetime.now(),
        "result": result
    }
        
    return result

def get_weekly_forecast_recursive(start_date=None):
    """
    Generates a 7-day forecast where predictions feed back into the history
    for future days (Recursive Forecasting).
    """
    import pandas as pd
    import numpy as np
    
    if start_date is None:
        start_date = datetime.datetime.now() + timedelta(days=1)
    
    # 1. Fetch Location & Weather Batch
    lat, lon = get_latest_location_from_db()
    if not lat:
        lat, lon = 34.05, -118.25
        
    weather_map = fetch_weekly_weather_forecast(start_date, lat, lon)
    
    # 2. Load History ONCE
    # We will append to this DF as we predict forward
    history_df = get_recent_history(days=60)
    
    forecasts = []
    
    # 3. Recursive Loop
    current_date = start_date
    
    # Load models once
    clf, reg = None, None
    try:
        clf, reg = load_models()
    except Exception as e:
        logger.error(f"Recursive Forecast: Failed to load models: {e}")
        pass # Will fall back to heuristic in loop

    for i in range(7):
        date_str = current_date.strftime("%Y-%m-%d")
        day_weather = weather_map.get(date_str)
        
        # --- Prediction Logic (Inline/Modified to use rolling history) ---
        # Convert to pandas Timestamp to ensure .dayofweek works
        pd_date = pd.to_datetime(current_date)
        X, meta = construct_features(pd_date, history_df, manual_weather=day_weather)
        
        predicted_pain = 0.0
        prob = 0.0
        risk = "Unknown"
        source = "live"
        
        if clf and reg:
            try:
                # Reorder
                if hasattr(clf, 'feature_names_in_'):
                    X = X[clf.feature_names_in_]
                
                probs = clf.predict_proba(X)[0]
                prob = probs[1]
                
                if prob > 0.6: risk = "High"
                elif prob > 0.2: risk = "Moderate"
                else: risk = "Low"
                
                if prob > 0.2:
                    pred_log = reg.predict(X)[0]
                    predicted_pain = max(0, min(10, np.expm1(pred_log)))
                
                source = meta.get('source', 'live') + " (ML)"
                
            except Exception as e:
                logger.error(f"Recursion ML error: {e}")
                # Fallback to Heuristic
                from .heuristic_predictor import HeuristicPredictor
                predictor = HeuristicPredictor({}) 
                
                heuristic_weather = {
                    'pressure_change': meta.get('pres_change', 0.0),
                    'prcp': meta.get('prcp', 0.0),
                    'average_humidity': meta.get('average_humidity', 50.0)
                }
                
                # Get yesterday pain from X or history
                yesterday_pain = 0.0
                if isinstance(X, pd.DataFrame) and 'Pain_Lag_1' in X.columns:
                     yesterday_pain = float(X.iloc[0]['Pain_Lag_1'])
                
                pred = predictor.predict(heuristic_weather, yesterday_pain, 0.0, 0.0)
                prob = pred['probability']
                risk = pred['risk_level']
                source = "Heuristic (Fallback)"
        else:
            # Fallback (Models not loaded)
            from .heuristic_predictor import HeuristicPredictor
            predictor = HeuristicPredictor({})
            heuristic_weather = {
                    'pressure_change': meta.get('pres_change', 0.0),
                    'prcp': meta.get('prcp', 0.0),
                    'average_humidity': meta.get('average_humidity', 50.0)
                }
            yesterday_pain = 0.0
            if isinstance(X, pd.DataFrame) and 'Pain_Lag_1' in X.columns:
                    yesterday_pain = float(X.iloc[0]['Pain_Lag_1'])
            
            pred = predictor.predict(heuristic_weather, yesterday_pain, 0.0, 0.0)
            prob = pred['probability']
            risk = pred['risk_level']
            source = "Heuristic (Fallback)"
            
        # 4. APPEND Prediction to History to effectively "Simulate" the future becoming past
        # We append a new row with the PREDICTED pain level.
        new_row = pd.DataFrame([{
            'Date': current_date,
            'Pain Level': predicted_pain
        }])
        
        # Concat is expensive but safe for 7 iterations
        history_df = pd.concat([history_df, new_row], ignore_index=True)
        
        forecasts.append({
            "date": date_str,
            "risk_probability": round(prob * 100, 1),
            "risk_level": risk,
            "source": source
        })
        
        current_date += timedelta(days=1)
        
    return forecasts

if __name__ == "__main__":
    # Test for tomorrow
    tomorrow = (datetime.datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Predicting for {tomorrow}...")
    result = get_prediction_for_date(tomorrow)
    print(result)

def get_hourly_forecast(start_date_str):
    """
    Returns a 24-hour risk forecast starting from the given date/time string.
    """
    import pandas as pd
    from datetime import datetime, timedelta
    from .heuristic_predictor import HeuristicPredictor
    
    # Parse Start Time (Round down to nearest hour)
    try:
        start_dt = pd.to_datetime(start_date_str).to_pydatetime()
    except:
        start_dt = datetime.now()
        
    # 1. Location
    lat, lon = get_latest_location_from_db()
    if not lat: lat, lon = 34.05, -118.25 # Default LA
    
    # 2. Fetch Data
    weather_hours = fetch_hourly_weather(start_dt, lat, lon, hours=24)
    circadian_profile = get_circadian_priors() # [p0, p1, ... p23]
    
    # 3. Check Medication (Last 12h)
    # We simply check if there's a valid med taken recently relative to NOW
    # Ideally we'd slide this window, but for a 24h forecast, the med effect decays rapidly.
    # We will compute "Hours Since Med" for the *start* of the forecast, 
    # and then increment it for each subsequent hour.
    
    # Fetch recent entries
    # TODO: This requires a service call or DB query. 
    # For now, simplistic DB query here.
    medication_recency_at_start = None
    try:
        conn = sqlite3.connect(DB_PATH)
        c = conn.cursor()
        # Look back 12 hours from start_dt
        lookback = start_dt - timedelta(hours=12)
        c.execute("SELECT Date, Time, Medications, Medication FROM migraine_log WHERE Date >= ?", (lookback.strftime('%Y-%m-%d'),))
        rows = c.fetchall()
        
        processed_meds = []
        import json
        
        for r in rows:
            r_date, r_time, r_meds_json, r_med_legacy = r
            entry_dt = pd.to_datetime(f"{r_date} {r_time}")
            
            # Check JSON
            found = False
            if r_meds_json:
                try:
                    mj = json.loads(r_meds_json)
                    if mj: found = True
                except:
                    pass
            # Check Legacy
            if not found and r_med_legacy:
                found = True
                
            if found:
                # Calculate hours until start_dt
                diff = (start_dt - entry_dt).total_seconds() / 3600.0
                if 0 <= diff <= 12:
                    processed_meds.append(diff)
        
        if processed_meds:
            medication_recency_at_start = min(processed_meds) # Most recent
            
        conn.close()
    except Exception as e:
        logger.warning(f"Med check failed: {e}")
        
    # 4. Generate Forecast
    predictor = HeuristicPredictor() # Default priors
    
    forecast_result = []
    
    # Temporary storage for calibration grouping
    # date_str -> list of (index_in_result, risk_value)
    daily_groups = {}
    
    for i, w in enumerate(weather_hours):
        # Time Management
        # w['time'] is ISO string
        try:
            current_hour_dt = datetime.fromisoformat(w['time'])
        except:
            current_hour_dt = start_dt + timedelta(hours=i)
            
        hour_idx = current_hour_dt.hour # 0-23
        date_key = current_hour_dt.strftime('%Y-%m-%d')
        
        # Circadian
        c_prob = circadian_profile[hour_idx]
        
        # Medication
        # If med was taken T hours ago at start, it is T+i hours ago now.
        m_recency = None
        if medication_recency_at_start is not None:
            m_recency = medication_recency_at_start + i
        
        # Predict
        pred = predictor.predict_hourly(
            weather_data=w,
            circadian_probability=c_prob,
            medication_recency=m_recency
        )
        
        risk_score = pred['probability'] * 100 # 0-100
        
        entry = {
            "time": w['time'],
            "risk_score": risk_score, # Will be calibrated
            "risk_level": pred['risk_level'],
            "temp": w['temp'],
            "humidity": w['humidity'],
            "prcp": w['prcp'],
            "details": pred['components']
        }
        forecast_result.append(entry)
        
        if date_key not in daily_groups:
            daily_groups[date_key] = []
        daily_groups[date_key].append( (len(forecast_result)-1, risk_score) )
        
    # 5. Calibrate against Daily ML Model
    # For each day involved in the hourly forecast, fetch the ML prediction (Anchor).
    # If Anchor > Peak_Hourly, scale the entire day up.
    
    for date_key, items in daily_groups.items():
        try:
            # Fetch Daily ML Prediction
            # This uses the specific date's weather + context
            daily_pred = get_prediction_for_date(date_key)
            if daily_pred:
                daily_prob = daily_pred['probability'] # 0-100
                
                # Find Peak in this group
                peak_hourly = max([val for idx, val in items]) if items else 0
                
                # If Daily Risk is significant (e.g. > 30%) and higher than hourly peak
                # We scale up. We rarely scale down to avoid hiding specific hourly triggers.
                if daily_prob > 30.0 and daily_prob > peak_hourly:
                    scale_factor = daily_prob / peak_hourly if peak_hourly > 5 else 1.0
                    
                    # Cap scaling to avoid absurdity (e.g. don't multiply by 10x)
                    scale_factor = min(scale_factor, 2.5) 
                    
                    # Apply Scaling
                    for idx, val in items:
                        new_score = val * scale_factor
                        # Hard Cap at 99%
                        new_score = min(new_score, 99.0)
                        
                        forecast_result[idx]['risk_score'] = round(new_score, 1)
                        
                        # Adjust Risk Level Label if needed
                        if new_score >= 60: forecast_result[idx]['risk_level'] = 'High'
                        elif new_score >= 30: forecast_result[idx]['risk_level'] = 'Moderate'
                        

                        
        except Exception as e:
            logger.error(f"Calibration error for {date_key}: {e}")
            
    return forecast_result

