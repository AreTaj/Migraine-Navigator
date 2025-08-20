import pandas as pd
from prediction.data_processing import convert_time_to_minutes, process_combined_data

def test_convert_time_to_minutes():
    assert convert_time_to_minutes("08:30") == 510
    assert convert_time_to_minutes("00:00") == 0
    assert convert_time_to_minutes(None) == 0

def test_process_combined_data_columns():
    df = process_combined_data()
    # Check that engineered columns exist
    for col in [
        'tdiff', 'tavg', 'tavg_lag1', 'tavg_lag2',
        'humid.*tavg', 'pres_change_lag1', 'pres_change_lag2',
        'Pain_Level_Log', 'Pain_Level_Binary'
    ]:
        assert col in df.columns
    # Check that output is a DataFrame
    assert isinstance(df, pd.DataFrame)