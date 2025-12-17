import os
import sys
import pandas as pd
import numpy as np
import itertools
from datetime import datetime, timedelta

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prediction.predict_future import load_models, construct_features

def maximize_risk():
    print("Loading models...")
    try:
        clf, reg = load_models()
    except Exception as e:
        print(f"Failed to load models: {e}")
        return

    print("Models loaded. Starting Grid Search for Maximum Risk...")

    # 1. Define Grid
    # Weather factors
    temps = [5.0, 15.0, 25.0, 35.0] # Cold to Hot
    pressures = [990.0, 1000.0, 1015.0, 1030.0] # Low to High
    humidities = [20.0, 50.0, 80.0] # Dry to Humid
    pres_changes = [-5.0, -2.0, 0.0, 2.0, 5.0] # Drop vs Rise
    
    # Lifestyle factors (Scale 0-3 / 1-3)
    sleeps = [1.0, 2.0, 3.0] # Poor, Fair, Good
    activities = [0.0, 1.0, 2.0, 3.0] # None, Light, Mod, Heavy

    # History Lag factors (0-10 Pain)
    # We will simulate "Avg Lag 1-7 days"
    # Low Pain History vs High Pain History
    pain_histories = [0.0, 3.0, 7.0, 9.0] 

    # Day of Week (0=Monday, 6=Sunday)
    days_of_week = list(range(7))

    best_risk = -1.0
    best_combo = None
    
    # Mock efficient history DataFrame
    # We won't pass a real DF to construct_features every time to save speed.
    # Instead, we will construct one basic feature set and then mutate X directly.
    
    # Base target date
    target_date = pd.Timestamp(datetime.now() + timedelta(days=1))
    
    # Create a dummy history DF just to satisfy the function signature
    dummy_history = pd.DataFrame({
        'Date': [datetime.now() - timedelta(days=i) for i in range(30)],
        'Pain Level': [0] * 30
    })

    # Get Feature Names from Model
    feature_names = clf.feature_names_in_ if hasattr(clf, 'feature_names_in_') else None
    
    count = 0
    total_combos = len(temps) * len(pressures) * len(humidities) * len(pres_changes) * len(sleeps) * len(activities) * len(pain_histories) * len(days_of_week)
    
    print(f"Testing {total_combos} combinations...")

    for t, p, h, dP, s, a, pain, day in itertools.product(temps, pressures, humidities, pres_changes, sleeps, activities, pain_histories, days_of_week):
        count += 1
        
        # 1. Weather Mock
        weather_mock = {
            'id': -1,
            'tavg': t,
            'tmin': t - 5,
            'tmax': t + 5,
            'pres': p,
            'pres_change': dP,
            'prcp': 0.0,
            'wspd': 10.0,
            'tsun': 600.0,
            'average_humidity': h,
            'midday_humidity': h,
            'source': 'simulation'
        }

        # 2. Construct Base Features
        # We perform construction once per loop (optimized? no, this is fast enough for 5k combos)
        # Note: construct_features uses target_date for DayOfWeek. We will overwrite it.
        X, _ = construct_features(target_date, dummy_history, manual_weather=weather_mock)
        
        # 3. OVERWRITE Features with Loop Variables
        # Lifestyle
        X['Sleep'] = s
        X['Physical Activity'] = a
        
        # Day of Week Overrides
        X['DayOfWeek'] = day
        X['DayOfWeek_sin'] = np.sin(2 * np.pi * day / 7)
        X['DayOfWeek_cos'] = np.cos(2 * np.pi * day / 7)
        
        # History Lags (Simulate recent history)
        # We overwrite all lag/rolling features to the 'pain' value
        for col in X.columns:
            if 'Pain_Lag' in col or 'Pain_Rolling' in col:
                X[col] = pain
                
        # 4. Predict
        if feature_names is not None:
             X = X[feature_names]
             
        if count % 5000 == 0:
            print(f"Processed {count} / {total_combos}...")
            
        prob = clf.predict_proba(X)[0][1] # Probability of Class 1 (Migraine)
        
        if prob > best_risk:
            best_risk = prob
            best_combo = {
                'Temp': t,
                'Pressure': p,
                'Humidity': h,
                'Pres_Change': dP,
                'Sleep': s,
                'Activity': a,
                'Recent_Pain': pain,
                'Day_Of_Week': day,
                'Risk_Prob': prob
            }
            # print(f"New Max Found: {prob:.4f} with {best_combo}")

    print("\n--- OPTIMIZATION RESULT ---")
    print(f"MAXIMUM RISK: {best_risk * 100:.1f}%")
    print("Conditions for Max Risk:")
    for k, v in best_combo.items():
        if k == 'Day_Of_Week':
            days = ['Monday', 'Tuesday', 'Wednesday', 'Thursday', 'Friday', 'Saturday', 'Sunday']
            print(f"  {k}: {v} ({days[int(v)]})")
        else:
            print(f"  {k}: {v}")

if __name__ == "__main__":
    maximize_risk()
