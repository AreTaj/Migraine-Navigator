import pytest
import pandas as pd
import numpy as np
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forecasting.data_processing import process_combined_data

def test_lag_features_logic():
    """
    Verify that Pain_Lag_1 is actually Yesterday's pain.
    """
    # Create fake data
    dates = pd.date_range(start='2023-01-01', end='2023-01-10', freq='D')
    df = pd.DataFrame({'Date': dates})
    df['Pain Level'] = [0, 5, 0, 8, 2, 0, 0, 4, 0, 0] # Some pattern
    df['tavg'] = 20.0 # Dummy weather
    
    # Save to temp csv just to mock the reading process if needed, 
    # but actual function reads from file. 
    # Instead, let's mock the read steps or just test the logic directly if we extract it.
    # Since process_combined_data reads from file, let's create a temporary CSV for it.
    
    temp_csv = 'tests/temp_combined.csv'
    df.to_csv(temp_csv, index=False)
    
    try:
        # Run processing
        processed = process_combined_data(combined_data_filename=temp_csv)
        
        # Check Lags
        # Original: [0, 5, 0, 8, 2, 0, 0, 4, 0, 0]
        # Lag 1 should shift right by 1
        # [NaN, 0, 5, 0, 8, 2, 0, 0, 4, 0]
        
        # The function drops first 30 rows, so this test will fail if we don't have enough data!
        # process_combined_data has `df = df.iloc[30:]`
        
        # We need more data for the test to pass with that hardcoded drop
        dates_long = pd.date_range(start='2023-01-01', end='2023-03-01', freq='D')
        df_long = pd.DataFrame({'Date': dates_long})
        df_long['Pain Level'] = np.random.randint(0, 10, size=len(df_long))
        df_long['tavg'] = 20.0
        
        # Set specific values at the cutoff to verify
        # Row 30 (index 30) corresponds to date 2023-01-31 (0-indexed days)
        # Pain at index 29 is the lag for index 30.
        df_long.loc[29, 'Pain Level'] = 9
        df_long.loc[30, 'Pain Level'] = 1
        
        df_long.to_csv(temp_csv, index=False)
        
        processed = process_combined_data(combined_data_filename=temp_csv)
        
        # The first row in processed should be what was originally index 30
        first_row = processed.iloc[0]
        
        # Verify Lag 1
        assert first_row['Pain_Lag_1'] == 9.0, f"Expected Lag_1 to be 9, got {first_row['Pain_Lag_1']}"
        assert first_row['Pain Level'] == 1.0, f"Expected Pain Level to be 1, got {first_row['Pain Level']}"
        
        print("Lag feature test passed!")
        
    finally:
        if os.path.exists(temp_csv):
            os.remove(temp_csv)

if __name__ == "__main__":
    test_lag_features_logic()
