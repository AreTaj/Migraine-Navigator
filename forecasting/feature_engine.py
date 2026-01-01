from datetime import timedelta
from typing import Dict, Any, Tuple, Optional, List
import logging

logger = logging.getLogger("feature_engine")

class FeatureEngine:
    @staticmethod
    def get_pain_lag(target_date, pain_map, days_ago):
        d = target_date.date() - timedelta(days=days_ago)
        return pain_map.get(d, 0.0)

    @staticmethod
    def construct_features(target_date, history_df, weather_data: Optional[Dict[str, Any]] = None) -> Tuple[Any, Dict[str, Any]]:
        """
        Builds a single-row DataFrame of features for the target_date.
        Uses history_df to calculate lags.
        
        LAZY LOADING: Imports pandas/numpy internally to avoid blocking app startup.
        """
        import pandas as pd
        import numpy as np
        
        features = {}
        
        # 1. Temporal Features (Cyclical Encoding)
        features['DayOfWeek'] = target_date.dayofweek
        features['Month'] = target_date.month
        features['DayOfWeek_sin'] = np.sin(2 * np.pi * features['DayOfWeek'] / 7)
        features['DayOfWeek_cos'] = np.cos(2 * np.pi * features['DayOfWeek'] / 7)
        features['Month_sin'] = np.sin(2 * np.pi * features['Month'] / 12)
        features['Month_cos'] = np.cos(2 * np.pi * features['Month'] / 12)
        
        # 2. Weather Integration
        weather = weather_data if weather_data else {}
        if 'source' not in weather:
             # If caller passed None/empty, we assume it's missing or handled upstream
             # But for feature construction we just set defaults if missing
             weather['source'] = 'unknown'

        features.update(weather)
        
        # Derived Weather
        features['tdiff'] = features.get('tmax', 25) - features.get('tmin', 15)
        features['humid.*tavg'] = features.get('average_humidity', 50) * features.get('tavg', 20)
        features['pres_change_lag1'] = 0.0 
        features['tavg_lag1'] = features.get('tavg', 20)
        
        # 3. Autoregressive (Lags)
        pain_map = dict(zip(history_df['Date'].dt.date, history_df['Pain Level']))
        
        features['Pain_Lag_1'] = FeatureEngine.get_pain_lag(target_date, pain_map, 1)
        features['Pain_Lag_2'] = FeatureEngine.get_pain_lag(target_date, pain_map, 2)
        features['Pain_Lag_3'] = FeatureEngine.get_pain_lag(target_date, pain_map, 3)
        features['Pain_Lag_7'] = FeatureEngine.get_pain_lag(target_date, pain_map, 7)
        
        last_30_vals = []
        for i in range(1, 31):
            last_30_vals.append(FeatureEngine.get_pain_lag(target_date, pain_map, i))
        
        features['Pain_Rolling_Mean_3'] = np.mean(last_30_vals[:3])
        features['Pain_Rolling_Mean_7'] = np.mean(last_30_vals[:7])
        features['Pain_Rolling_Mean_30'] = np.mean(last_30_vals)
        
        # Defaults
        features['Sleep'] = 2.0 
        features['Physical Activity'] = 1.5 
        
        return pd.DataFrame([features]), features

    @staticmethod
    def get_circadian_priors(df) -> List[float]:
        """
        Analyzes historical start times to build 24h risk distribution.
        """
        import pandas as pd
        import numpy as np
        
        if df.empty:
            return [0.1] * 24 
            
        pain_df = df[pd.to_numeric(df['Pain Level'], errors='coerce') > 0].copy()
        if pain_df.empty:
            return [0.1] * 24
            
        valid_hours = []
        for t_str in pain_df['Time']:
            try:
                if pd.isna(t_str): continue
                h = int(str(t_str).split(':')[0])
                valid_hours.append(h)
            except:
                continue
                
        if not valid_hours:
            return [0.1] * 24
            
        counts = np.bincount(valid_hours, minlength=24)
        total = len(valid_hours)
        probs = counts / total
        
        smoothed_probs = np.zeros(24)
        for i in range(24):
            prev_i = (i - 1) % 24
            next_i = (i + 1) % 24
            p = (probs[prev_i]*0.2) + (probs[i]*0.6) + (probs[next_i]*0.2)
            smoothed_probs[i] = p
            
        max_p = np.max(smoothed_probs)
        if max_p > 0:
            smoothed_probs = (smoothed_probs / max_p) * 0.8
        else:
            smoothed_probs = np.full(24, 0.1)
            
        return smoothed_probs.tolist()
