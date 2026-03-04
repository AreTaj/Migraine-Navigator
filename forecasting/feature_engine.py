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
    def select_features_by_correlation(X, threshold=0.90):
        """
        Drops one feature from each pair that exceeds the Pearson correlation threshold.
        
        Tie-breaking: drops the feature with more NaN values.
        If tied, drops the alphabetically-last column name for determinism.
        
        Returns (selected_cols, dropped_cols) as lists of column names.
        Skips filtering entirely if fewer than 30 rows (unreliable correlations).
        """
        import pandas as pd

        MIN_ROWS = 30

        if len(X) < MIN_ROWS:
            logger.info(f"Feature selection skipped: insufficient data (N={len(X)}, need {MIN_ROWS}).")
            return list(X.columns), []

        numeric_X = X.select_dtypes(include='number')
        if numeric_X.empty:
            return list(X.columns), []

        corr_matrix = numeric_X.corr(method='pearson').abs()

        # Collect correlated pairs from upper triangle
        pairs = []
        cols = corr_matrix.columns
        for i in range(len(cols)):
            for j in range(i + 1, len(cols)):
                val = corr_matrix.iloc[i, j]
                if pd.isna(val) or val <= threshold:
                    continue
                pairs.append((cols[i], cols[j], val))

        # Sort for deterministic iteration order
        pairs.sort(key=lambda x: (x[0], x[1]))

        to_drop = set()
        for col_a, col_b, val in pairs:
            if col_a in to_drop or col_b in to_drop:
                continue

            nans_a = numeric_X[col_a].isna().sum()
            nans_b = numeric_X[col_b].isna().sum()

            if nans_a > nans_b:
                to_drop.add(col_a)
            elif nans_b > nans_a:
                to_drop.add(col_b)
            else:
                # Alphabetical tie-break: drop the one that sorts last
                to_drop.add(max(col_a, col_b))

        dropped = sorted(to_drop)
        selected = [c for c in X.columns if c not in to_drop]

        if dropped:
            logger.info(f"Feature selection dropped {len(dropped)} feature(s): {dropped}")

        return selected, dropped

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
