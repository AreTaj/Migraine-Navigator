import pandas as pd
import numpy as np
import os

weather_data_filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'weather_data.csv')
migraine_data_filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'migraine_log.csv')
combined_data_filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'combined_data.csv')

import sqlite3

def load_migraine_log_from_db(db_path='data/migraine_log.db'):
    """
    Loads migraine log data from the SQLite database into a pandas DataFrame.

    Args:
        db_path (str): Path to the SQLite database file."""
    conn = sqlite3.connect('data/migraine_log.db')
    c = conn.cursor()
    c.execute("SELECT * FROM migraine_log")
    rows = c.fetchall()
    conn.close()
    return rows

def merge_migraine_and_weather_data(migraine_log_file=migraine_data_filename, weather_data_file=weather_data_filename, output_file=combined_data_filename):
    migraine_data = pd.read_csv(migraine_log_file)
    weather_data = pd.read_csv(weather_data_file)
    combined_data = pd.merge(migraine_data, weather_data, left_on='Date', right_on='date', how='left')
    combined_data.to_csv(output_file, index=False)

def convert_time_to_minutes(time_str):
    if pd.isna(time_str):
        return 0
    h, m = map(int, time_str.split(':'))
    return h * 60 + m

def process_combined_data(combined_data_filename=combined_data_filename):
    """
    Loads the combined migraine and weather data, performs feature engineering, and returns a processed DataFrame.

    Returns:
        pd.DataFrame: The processed DataFrame ready for modeling.
    """
    combined_data = pd.read_csv(combined_data_filename)

    # Convert time to minutes since midnight
    combined_data['Time'] = combined_data['Time'].apply(convert_time_to_minutes)

    # Parse date and extract date-based features
    combined_data['Date'] = pd.to_datetime(combined_data['Date'])
    combined_data['DayOfWeek'] = combined_data['Date'].dt.dayofweek  # 0=Monday
    combined_data['Month'] = combined_data['Date'].dt.month

    # One-hot encode categorical features
    combined_data = pd.get_dummies(combined_data, columns=['DayOfWeek', 'Month'])
    combined_data = pd.get_dummies(combined_data, columns=['Sleep', 'Physical Activity'])

    # Feature engineering: temperature difference
    combined_data['tdiff'] = combined_data['tmax'] - combined_data['tmin']

    # Feature engineering: average temperature
    combined_data['tavg'] = (combined_data['tmax'] + combined_data['tmin']) / 2

    # Feature engineering: lag features for average temperature
    combined_data['tavg_lag1'] = combined_data['tavg'].shift(1)
    combined_data['tavg_lag2'] = combined_data['tavg'].shift(2)

    # Feature engineering: interaction between humidity and average temperature
    combined_data['humid.*tavg'] = combined_data['average_humidity'] * combined_data['tavg']

    if 'pres_change' in combined_data.columns:
        combined_data['pres_change_lag1'] = combined_data['pres_change'].shift(1)
        combined_data['pres_change_lag2'] = combined_data['pres_change'].shift(2)
    else:
        combined_data['pres_change_lag1'] = None
        combined_data['pres_change_lag2'] = None

    # Clean and transform pain level
    combined_data['Pain Level'] = pd.to_numeric(combined_data['Pain Level'], errors='coerce').fillna(0)
    # Log-transform pain level for regression tasks
    combined_data['Pain_Level_Log'] = np.log1p(combined_data['Pain Level'])

    # Binary pain level for classification tasks
    combined_data['Pain_Level_Binary'] = (combined_data['Pain Level'] > 0).astype(int)

    return combined_data.copy()