import os
import sqlite3
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    import pandas as pd
    import numpy as np

# Define paths
from api.utils import get_data_dir

# Define paths
data_dir = get_data_dir()
weather_data_filename = os.path.join(data_dir, 'weather_data.csv')
migraine_data_filename = os.path.join(data_dir, 'migraine_log.csv')
combined_data_filename = os.path.join(data_dir, 'combined_data.csv')

def load_migraine_log_from_db(db_path=None):
    """
    Loads migraine log data from the SQLite database into a pandas DataFrame.
    """
    import pandas as pd
    from api.utils import get_db_path
    if db_path is None:
        db_path = get_db_path()
        
    conn = sqlite3.connect(db_path)
    # c = conn.cursor() # Not needed for pandas read_sql
    query = "SELECT * FROM migraine_log"
    df = pd.read_sql_query(query, conn)
    conn.close()
    return df

def merge_migraine_and_weather_data(migraine_log_file=migraine_data_filename, weather_data_file=weather_data_filename, output_file=combined_data_filename, db_path=None, return_df=False):
    """
    Merges migraine and weather data, ensuring a continuous daily timeline.
    Crucially, it treats missing days in the migraine log as 'No Pain'.
    Note: Reads from SQLite DB by default now, though allows file override if needed (but we ignore csv arg mostly).
    """
    # Load from DB instead of CSV
    import pandas as pd
    migraine_data = load_migraine_log_from_db(db_path)
    if os.path.exists(weather_data_file):
        weather_data = pd.read_csv(weather_data_file)
    else:
        # Fallback if no weather data in test env
        weather_data = pd.DataFrame({'date': [], 'tavg': []}) 
        
    # Standardize dates
    migraine_data['Date'] = pd.to_datetime(migraine_data['Date'])
    weather_data['date'] = pd.to_datetime(weather_data['date'])
    
    # create a full date range from the start of data to today (or max date)
    min_date = min(migraine_data['Date'].min(), weather_data['date'].min())
    max_date = max(migraine_data['Date'].max(), weather_data['date'].max())
    full_date_range = pd.date_range(start=min_date, end=max_date, freq='D')
    
    # Create the template dataframe
    full_df = pd.DataFrame({'Date': full_date_range})
    
    # Merge migraine data onto the full timeline
    # Aggregation Strategy: Max for Pain, Mean for Sleep/Activity
    migraine_data['Pain Level'] = pd.to_numeric(migraine_data['Pain Level'], errors='coerce')
    migraine_data['Sleep'] = pd.to_numeric(migraine_data['Sleep'], errors='coerce')
    migraine_data['Physical Activity'] = pd.to_numeric(migraine_data['Physical Activity'], errors='coerce')
    
    # Identify numeric columns for aggregation
    agg_dict = {
        'Pain Level': 'max',
        'Sleep': 'mean', # Note: 'Sleep' in entries already refers to the night before the entry date.
        'Physical Activity': 'mean',
    }
    # Keep other columns if possible (take first)
    for col in migraine_data.columns:
        if col not in agg_dict and col != 'Date':
            agg_dict[col] = 'first'

    migraine_data = migraine_data.groupby('Date', as_index=False).agg(agg_dict)
    
    combined = pd.merge(full_df, migraine_data, on='Date', how='left')
    
    # Fill missing Pain Level with 0 (Assumption: Missing Log = No Pain)
    combined['Pain Level'] = combined['Pain Level'].fillna(0)
    
    # Merge weather data
    combined = pd.merge(combined, weather_data, left_on='Date', right_on='date', how='left')
    
    # Drop redundancy and save
    if 'date' in combined.columns:
        combined.drop(columns=['date'], inplace=True)
        
    combined.to_csv(output_file, index=False)
    
    if return_df:
        return combined
    return combined

def convert_time_to_minutes(time_str):
    import pandas as pd
    if pd.isna(time_str):
        return 0
    try:
        h, m = map(int, str(time_str).split(':'))
        return h * 60 + m
    except:
        return 0

def process_combined_data(combined_data_filename=combined_data_filename, input_df=None):
    """
    Loads combined data, performs feature engineering including lags and rolling means.
    Can accept a direct DataFrame for testing/pipeline integration without reading from CSV.
    """
    import pandas as pd
    import numpy as np
    if input_df is not None:
        df = input_df.copy()
    else:
        df = pd.read_csv(combined_data_filename)
        
    if 'Date' in df.columns and not pd.api.types.is_datetime64_any_dtype(df['Date']):
        df['Date'] = pd.to_datetime(df['Date'])
    
    # Sort just in case
    df = df.sort_values('Date').reset_index(drop=True)

    # --- Feature Engineering ---

    # 1. Temporal Features
    df['DayOfWeek'] = df['Date'].dt.dayofweek
    df['Month'] = df['Date'].dt.month
    
    # Cyclical encoding for Time (DayOfWeek, Month)
    df['DayOfWeek_sin'] = np.sin(2 * np.pi * df['DayOfWeek'] / 7)
    df['DayOfWeek_cos'] = np.cos(2 * np.pi * df['DayOfWeek'] / 7)
    df['Month_sin'] = np.sin(2 * np.pi * df['Month'] / 12)
    df['Month_cos'] = np.cos(2 * np.pi * df['Month'] / 12)

    # 2. Weather Features
    # Handle missing weather data (forward fill, then backward fill)
    weather_cols = ['tavg', 'tmin', 'tmax', 'prcp', 'snow', 'wdir', 'wspd', 'wpgt', 'pres', 'tsun']
    for col in weather_cols:
        if col in df.columns:
            df[col] = df[col].ffill().bfill() # Fill gaps

    if 'tmax' in df.columns and 'tmin' in df.columns:
        df['tdiff'] = df['tmax'] - df['tmin']
        df['tavg'] = (df['tmax'] + df['tmin']) / 2
    
    # Weather Interaction
    if 'average_humidity' in df.columns and 'tavg' in df.columns:
        df['humid.*tavg'] = df['average_humidity'].fillna(0) * df['tavg']

    # 3. Autoregressive Features (Lags)
    df['Pain_Lag_1'] = df['Pain Level'].shift(1)
    df['Pain_Lag_2'] = df['Pain Level'].shift(2)
    df['Pain_Lag_3'] = df['Pain Level'].shift(3)
    df['Pain_Lag_7'] = df['Pain Level'].shift(7) # Weekly pattern check

    # Rolling stats
    df['Pain_Rolling_Mean_3'] = df['Pain Level'].shift(1).rolling(window=3).mean()
    df['Pain_Rolling_Mean_7'] = df['Pain Level'].shift(1).rolling(window=7).mean()
    df['Pain_Rolling_Mean_30'] = df['Pain Level'].shift(1).rolling(window=30).mean()
    
    # Lagged Weather (Weather often triggers migraines with a delay)
    if 'pres' in df.columns:
        df['pres_change'] = df['pres'].diff()
        df['pres_change_lag1'] = df['pres_change'].shift(1)
    
    if 'tavg' in df.columns:
        df['tavg_lag1'] = df['tavg'].shift(1)

    # 4. Target Transformations
    df['Pain_Level_Binary'] = (df['Pain Level'] > 0).astype(int)
    # Log transform for regression stability, but handle 0s
    df['Pain_Level_Log'] = np.log1p(df['Pain Level'])

    # Drop rows with NaN created by shifting (first 30 rows)
    df = df.iloc[30:].reset_index(drop=True)

    return df