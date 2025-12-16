
import pytest
import pandas as pd
import numpy as np
import sys
import os
import joblib
from datetime import datetime
from unittest.mock import patch, MagicMock

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from prediction.predict_future import construct_features, load_models

def test_feature_sensitivity(capsys):
    """
    Tests the sensitivity of the model to individual feature changes and scenarios.
    Prints a report of how changing features affects the predicted probability and pain level.
    """
    
    # 1. Setup Mock Data
    target_date = pd.to_datetime('2023-06-15') # Random date
    
    # Mock history dataframe - HIGH RISK BASELINE (Recent Migraines)
    dates = pd.date_range(end=target_date, periods=60, freq='D')
    history_df = pd.DataFrame({'Date': dates})
    # Most days distinct 0, but recent days (end of array) high pain
    history_df['Pain Level'] = 0
    # Set pain for yesterday and few days ago
    history_df.loc[58, 'Pain Level'] = 8 # Yesterday
    history_df.loc[56, 'Pain Level'] = 6 # 3 days ago
    
    # Mock Weather - Stable Summer Day
    mock_weather = {
        'id': -1,
        'tavg': 25.0,
        'tmin': 20.0,
        'tmax': 30.0,
        'prcp': 0.0,
        'wspd': 10.0,
        'pres': 1015.0,
        'tsun': 800.0,
        'average_humidity': 50.0,
        'pres_change': 0.0,
        'midday_humidity': 50.0
    }
    
    # Mock dependencies
    with patch('prediction.predict_future.get_latest_location_from_db', return_value=(40.7128, -74.0060)), \
         patch('prediction.predict_future.fetch_weather_forecast', return_value=mock_weather):
         
        # 2. Get Baseline Features
        baseline_X, _ = construct_features(target_date, history_df)
    
    # 3. Load actual models
    try:
        clf, reg = load_models()
    except FileNotFoundError:
        pytest.skip("Models not found. Skipping sensitivity test.")

    # Align columns
    if hasattr(clf, 'feature_names_in_'):
        baseline_X = baseline_X[clf.feature_names_in_]
        
    # Helper to predict
    def get_pred(X_in):
        prob = clf.predict_proba(X_in)[0][1]
        log_pain = reg.predict(X_in)[0]
        pain = np.expm1(log_pain)
        pain = max(0, min(10, pain))
        return prob, pain

    base_prob, base_pain = get_pred(baseline_X)
    
    print("\n\n--- Sensitivity Analysis Report (High Risk Baseline) ---")
    print(f"Baseline Probability: {base_prob:.4f}")
    print(f"Baseline Predicted Pain: {base_pain:.4f}")
    print("-" * 75)
    print(f"{'Scenario / Feature':<30} | {'Change':<20} | {'Prob Delta':<10} | {'Pain Delta':<10}")
    print("-" * 75)

    # 5. Iterate and Perturb Single Features
    features = baseline_X.columns.tolist()
    
    # Define meaningful perturbations override
    perturbations = {
        'pres': -10.0, # Drop 10 hPa
        'tavg': +5.0, # Hotter
        'average_humidity': +20.0, # Much more humid
        'Pain_Lag_1': -8.0, # What if NO pain yesterday? (Removing the trigger)
        'prcp': +5.0, # Rain
    }

    for feature in features:
        # Create a copy
        modified_X = baseline_X.copy()
        val = modified_X[feature].iloc[0]
        
        # Determine perturbation
        if feature in perturbations:
            delta = perturbations[feature]
            new_val = val + delta
            desc = f"{delta:+.1f}"
        else:
             # Default logic
            if feature in ['DayOfWeek', 'Month']:
                new_val = val + 1
                desc = "+1 unit"
            elif abs(val) < 1e-5:
                 new_val = 1.0
                 desc = "0->1"
            else:
                new_val = val * 1.10
                desc = "+10%"
            
        modified_X[feature] = new_val
        
        # Predict
        new_prob, new_pain = get_pred(modified_X)
        
        prob_delta = new_prob - base_prob
        pain_delta = new_pain - base_pain
        
        # Highlight significant changes?
        marker = ""
        if abs(prob_delta) > 0.05 or abs(pain_delta) > 0.5:
             marker = " <--"

        print(f"{feature:<30} | {desc:<20} | {prob_delta:<+10.4f} | {pain_delta:<+10.4f} {marker}")

    # 6. Complex Scenarios
    print("-" * 75)
    
    # Scenario: Storm (Low Pressure, Rain, Wind, Negative Pres Trend)
    storm_X = baseline_X.copy()
    storm_X['pres'] = 1000.0 # Low
    if 'pres_change' in storm_X.columns: storm_X['pres_change'] = -5.0 # Dropping fast
    if 'prcp' in storm_X.columns: storm_X['prcp'] = 10.0 # Heavy rain
    if 'wspd' in storm_X.columns: storm_X['wspd'] = 30.0 # Windy
    if 'average_humidity' in storm_X.columns: storm_X['average_humidity'] = 90.0 # Humid
    
    s_prob, s_pain = get_pred(storm_X)
    print(f"{'SCENARIO: Storm':<30} | {'Multi-factor':<20} | {(s_prob - base_prob):<+10.4f} | {(s_pain - base_pain):<+10.4f} <--")

    print("-" * 75)
    print("Report Complete.\n")
    
    # Assert nothing crashed
    assert len(features) > 0
