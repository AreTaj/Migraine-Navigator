import os
import sqlite3
import datetime
from datetime import timedelta
from typing import TYPE_CHECKING, Dict, Any
import sys
import logging

# --- NEW IMPORTS ---
from services.weather_service import WeatherService
from forecasting.feature_engine import FeatureEngine
from forecasting.data_loader import get_recent_history, get_latest_location_from_db
from api.utils import get_db_path, get_data_dir

# Lazy loaded types
if TYPE_CHECKING:
    import pandas as pd
    import numpy as np
    import joblib

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
MODEL_DIR = os.path.join(BASE_DIR, '..', 'models')
MODEL_CLF_PATH = os.path.join(MODEL_DIR, 'best_model_clf.pkl')
MODEL_REG_PATH = os.path.join(MODEL_DIR, 'best_model_reg.pkl')
TESTER_CLF_PATH = os.path.join(MODEL_DIR, 'tester_model_clf.pkl')
TESTER_REG_PATH = os.path.join(MODEL_DIR, 'tester_model_reg.pkl')

# Calibration Constants
# Limits how much the Daily ML Truth can inflate the Hourly Heuristic shape.
# 2.5x allows a 20% heuristic to scale to 50%, but prevents 5% -> 50% (noise amplification).
MAX_CALIBRATION_SCALE = 2.5

# DB_PATH = get_db_path() # Removed global

# Setup logger
logger = logging.getLogger("inference")
handler = logging.FileHandler(os.path.join(get_data_dir(), "api_debug.log"))
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)
console_handler = logging.StreamHandler(sys.stdout)
console_handler.setFormatter(formatter)
logger.addHandler(console_handler)
logger.setLevel(logging.DEBUG)

_clf_model = None
_reg_model = None
_tester_clf_model = None
_tester_reg_model = None
_prediction_cache = {}

def load_models(tester_mode=False):
    global _clf_model, _reg_model, _tester_clf_model, _tester_reg_model
    
    import joblib
    
    if tester_mode:
        if _tester_clf_model is None:
            if not os.path.exists(TESTER_CLF_PATH):
                raise FileNotFoundError("Tester Model files not found")
            logger.debug("Loading TESTER CLF model...")
            _tester_clf_model = joblib.load(TESTER_CLF_PATH)
            logger.debug("Loading TESTER REG model...")
            _tester_reg_model = joblib.load(TESTER_REG_PATH)
        return _tester_clf_model, _tester_reg_model
    
    else:
        # Production / Local Mode
        if _clf_model is None:
            if not os.path.exists(MODEL_CLF_PATH):
                # Graceful degradation for new users who haven't trained yet
                # We return None, logic below must handle it
                return None, None
            
            logger.debug("Loading CLF model...")
            try:
                _clf_model = joblib.load(MODEL_CLF_PATH)
                logger.debug("Loading REG model...")
                _reg_model = joblib.load(MODEL_REG_PATH)
            except Exception as e:
                logger.error(f"Error loading models: {e}")
                return None, None
                
        return _clf_model, _reg_model

def clear_prediction_cache():
    global _prediction_cache
    _prediction_cache.clear()
    logger.info("Prediction cache cleared.")

def get_prediction_for_date(target_date_str, weather_override=None, db_path=None):
    if db_path is None: db_path = get_db_path() # Fallback for non-request calls
    logger.debug(f"Starting prediction for {target_date_str} with DB: {os.path.basename(db_path)}")
    
    # 1. Check Cache
    if target_date_str in _prediction_cache:
        # Simple TTL check (1 hour) could go here
        return _prediction_cache[target_date_str]["result"]

    try:
        import pandas as pd
        import numpy as np
    except ImportError as e:
        logger.error(f"Failed to import pandas/numpy: {e}")
        raise e
        
    target_date = pd.to_datetime(target_date_str)
    
    # 2. Coordinate Data Fetching
    # A. History
    history = get_recent_history(db_path)
    
    # B. Weather
    weather = weather_override
    if not weather:
        lat, lon = get_latest_location_from_db(db_path)
        if lat and lon:
            weather = WeatherService.fetch_forecast(lat, lon, target_date)
            if weather:
                weather['Latitude'] = lat
                weather['Longitude'] = lon
                if 'source' not in weather:
                    weather['source'] = 'live'
            else:
                 # Fallback logic could be moved to Service or kept here as business rule
                 # For now, we keep simpler service and handle fallback if needed or let FeatureEngine handle defaults
                 pass
    
    # C. Features
    X, meta = FeatureEngine.construct_features(target_date, history, weather_data=weather)
    
    # 3. Predict (ML Inference)
    try:
        # Check Force Heuristic Mode
        force_heuristic = False
        try:
             conn = sqlite3.connect(db_path)
             cursor = conn.cursor()
             cursor.execute("SELECT value FROM user_settings WHERE key='force_heuristic_mode'")
             row = cursor.fetchone()
             if row and str(row[0]).lower() == 'true':
                 force_heuristic = True
             conn.close()
        except Exception: pass

        if force_heuristic:
             logger.info("Force Heuristic Mode enabled. Bypassing ML.")
             return _run_heuristic_fallback(target_date_str, X, meta, db_path)

        # detect mode
        is_tester = 'synthetic' in os.path.basename(db_path)
        clf, reg = load_models(tester_mode=is_tester)
        
        if clf is None or reg is None:
            logger.info("No ML models available. Falling back to Heuristic.")
             # Raise exception to trigger the heuristic fallback catch block below
            raise FileNotFoundError("No models found")
        
        # Safe column ordering
        if hasattr(clf, 'feature_names_in_'):
            X = X[clf.feature_names_in_]
            
        probs = clf.predict_proba(X)[0]
        prob_migraine = probs[1]
        
        pred_log_pain = reg.predict(X)[0]
        pred_pain = np.expm1(pred_log_pain) 
        pred_pain = max(0, min(10, pred_pain))
        
        risk = "Low"
        if prob_migraine > 0.6: risk = "High"
        elif prob_migraine > 0.2: risk = "Moderate"
            
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
        result = _run_heuristic_fallback(target_date_str, X, meta, db_path)
        
    # Update Cache
    _prediction_cache[target_date_str] = {
        "timestamp": datetime.datetime.now(),
        "result": result
    }
    return result

def _run_heuristic_fallback(target_date_str, X, meta, db_path=None):
    if db_path is None: db_path = get_db_path()
    """
    Helper to run Heuristic Predictor when ML fails.
    """
    from .heuristic_predictor import HeuristicPredictor
    import pandas as pd
    
    # Fetch User Priors
    user_priors = {}
    try:
        conn = sqlite3.connect(db_path)
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT key, value FROM user_settings")
        rows = cursor.fetchall()
        for row in rows:
            try:
                user_priors[row['key']] = float(row['value'])
            except ValueError: pass
        conn.close()
    except Exception: pass

    predictor = HeuristicPredictor(user_priors)
    
    yesterday_pain = 0.0
    if isinstance(X, pd.DataFrame) and 'Pain_Lag_1' in X.columns:
        yesterday_pain = float(X.iloc[0]['Pain_Lag_1'])
    
    heuristic_weather = {
        'pressure_change': meta.get('pres_change', 0.0),
        'prcp': meta.get('prcp', 0.0),
        'average_humidity': meta.get('average_humidity', 50.0)
    }
    
    pred = predictor.predict(
        weather_data=heuristic_weather,
        yesterday_pain=yesterday_pain
    )
    
    return {
        "date": target_date_str,
        "probability": round(pred['probability'] * 100, 1),
        "risk_level": pred['risk_level'],
        "predicted_pain": 0.0,
        "source": meta.get('source', 'live') + " (Heuristic)",
        "components": pred.get('components', {})
    }

def get_weekly_forecast(start_date=None, db_path=None):
    if db_path is None: db_path = get_db_path()
    """
    Generates a 7-day forecast using Direct Forecasting.
    Each day is predicted independently using the same recent history, 
    isolating the weather impact.
    """
    import pandas as pd
    import numpy as np
    
    if start_date is None:
        start_date = datetime.datetime.now() + timedelta(days=1)
    
    lat, lon = get_latest_location_from_db(db_path)
    
    weather_map = {}
    if lat and lon:
        weather_map = WeatherService.fetch_weekly(start_date, lat, lon)
    
    # Get history ONCE. We will use this same history for all future days.
    # This assumes that "Recent History" is constant relative to the forecast window.
    base_history_df = get_recent_history(db_path, days=60)
    
    forecasts = []
    current_date = start_date
    
    
    # Check Force Heuristic Mode
    # (Removed redundant check since get_prediction_for_date handles it)
    
    for i in range(7):
        date_str = current_date.strftime("%Y-%m-%d")
        day_weather = weather_map.get(date_str)
        
        # Reuse the main prediction pipeline ensures 100% consistency
        # We inject the pre-fetched weather to avoid N+1 API calls
        try:
            pred = get_prediction_for_date(date_str, weather_override=day_weather, db_path=db_path)
            
            prob = float(pred.get('probability', 0.0)) / 100.0
            risk = pred.get('risk_level', 'Low')
            pred_pain = float(pred.get('predicted_pain', 0.0))
            
            # Debug log to verify consistency if needed
            # logger.info(f"Weekly Day {i}: {prob*100}% ({risk})")
            
        except Exception as e:
            logger.error(f"Weekly Prediction failed for {date_str}: {e}")
            prob = 0.1
            risk = "Low"
            pred_pain = 0.0

        forecasts.append({
            "date": date_str,
            "risk_probability": round(prob * 100, 1),
            "risk_level": risk,
            "predicted_pain": round(pred_pain, 1)
        })
        
        current_date += timedelta(days=1)
        
    return forecasts

def get_hourly_forecast(start_date_str, db_path=None):
    if db_path is None: db_path = get_db_path()
    import pandas as pd
    from .heuristic_predictor import HeuristicPredictor
    
    if start_date_str is None:
        start_date_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

    start_dt = pd.to_datetime(start_date_str)
    lat, lon = get_latest_location_from_db(db_path)
    if not lat: lat, lon = 34.05, -118.25 # Default LA
    
    full_hourly_weather = WeatherService.fetch_hourly(start_dt, lat, lon, hours=24)
    history_df = get_recent_history(db_path)
    circadian_priors = FeatureEngine.get_circadian_priors(history_df)
    
    # Init Heuristic
    predictor = HeuristicPredictor() # Load priors properly if needed
    
    results = []
    for w_hour in full_hourly_weather:
        # Determine hour index (0-23)
        t_obj = pd.to_datetime(w_hour['time'])
        hour_idx = t_obj.hour
        
        circadian_risk = circadian_priors[hour_idx]
        
        pred = predictor.predict_hourly(w_hour, circadian_risk)
        
        results.append({
            "time": w_hour['time'],
            "risk_score": round(pred['probability'] * 100, 1),
            "risk_level": pred['risk_level'],
            "temp": w_hour['temp'],
            "humidity": w_hour['humidity'],
            "desc": " clear", # simplified
            "details": pred['components']
        })
        
    # 5. Calibrate against Daily ML Model (Truth Propagation)
    # The Daily ML model contains the "Truth" (Magnitude) derived from history.
    # The Hourly Heuristic contains the "Shape" derived from weather/circadian.
    # We scale the Shape to match the Magnitude.
    
    # helper: grouping by date
    daily_groups = {}
    for idx, item in enumerate(results):
        # item['time'] is ISO string or close to it
        d_key = item['time'].split('T')[0]
        if d_key not in daily_groups:
            daily_groups[d_key] = []
        daily_groups[d_key].append(idx)

    for date_key, indices in daily_groups.items():
        try:
            # Fetch Daily ML Prediction (The Anchor)
            # We call the main prediction function which uses ML models
            # NOTE: Recursive check - get_prediction_for_date does NOT call get_hourly_forecast_recursive or similar
            # so this is safe.
            daily_pred = get_prediction_for_date(date_key, db_path=db_path)
            
            if daily_pred and daily_pred.get('probability') is not None:
                daily_prob = float(daily_pred['probability']) # 0-100
                
                # Find Peak in this group (Raw Heuristic)
                current_scores = [results[i]['risk_score'] for i in indices]
                peak_hourly = max(current_scores) if current_scores else 0.1
                
                # Apply V0.2.2 Logic:
                # If Daily Risk is significant (>30%) and higher than hourly peak,
                # we scale up. We do NOT scale down (triggers are triggers).
                if daily_prob > 30.0 and daily_prob > peak_hourly:
                    # Calculate Scale Factor
                    # Cap at MAX_CALIBRATION_SCALE to prevent exploding low-confidence heuristics
                    scale_factor = daily_prob / peak_hourly if peak_hourly > 5 else 1.0
                    scale_factor = min(scale_factor, MAX_CALIBRATION_SCALE)
                    
                    # Apply Scaling
                    for idx in indices:
                        old_score = results[idx]['risk_score']
                        new_score = old_score * scale_factor
                        
                        # Hard Cap at 99%
                        new_score = min(new_score, 99.0)
                        
                        results[idx]['risk_score'] = round(new_score, 1)
                        
                        # Update Level Label to match new score
                        if new_score >= 60: 
                            results[idx]['risk_level'] = 'High'
                        elif new_score >= 30: 
                            results[idx]['risk_level'] = 'Moderate'
                        else:
                            results[idx]['risk_level'] = 'Low'
                            
        except Exception as e:
            # Fail silently on calibration, fallback to raw heuristics is safe
            print(f"Calibration warning for {date_key}: {e}")

    return results

if __name__ == "__main__":
    # Test
    tomorrow = (datetime.datetime.now() + timedelta(days=1)).strftime("%Y-%m-%d")
    print(f"Predicting for {tomorrow}...")
    print(get_prediction_for_date(tomorrow))
