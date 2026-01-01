
import pytest
from unittest.mock import patch, MagicMock
import datetime
import pandas as pd
import sys
import os

# Ensure project root is in path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forecasting.inference import get_prediction_for_date

@pytest.fixture
def mock_weather_data():
    return {
        'id': -1,
        'tavg': 20.0,
        'tmin': 15.0,
        'tmax': 25.0,
        'prcp': 0.0,
        'wspd': 10.0,
        'pres': 1015.0,
        'tsun': 600.0,
        'average_humidity': 50.0,
        'pres_change': -2.0,
        'midday_humidity': 50.0,
        'source': 'mocked_service', # Distinct source to verify usage
        'Latitude': 34.05,
        'Longitude': -118.25
    }

@patch('services.weather_service.WeatherService.fetch_forecast')
@patch('forecasting.inference.get_recent_history')
@patch('forecasting.inference.get_latest_location_from_db')
def test_prediction_uses_mock_weather(mock_loc, mock_hist, mock_fetch, mock_weather_data):
    """
    Verifies that get_prediction_for_date calls WeatherService and uses its result.
    """
    # Setup Mocks
    mock_loc.return_value = (34.05, -118.25)
    
    # Mock History (Empty is fine, defaults will be used by FeatureEngine)
    mock_hist.return_value = pd.DataFrame({
        'Date': [datetime.datetime.now() - datetime.timedelta(days=1)],
        'Pain Level': [0]
    })
    
    # Setup WeatherService Mock
    mock_fetch.return_value = mock_weather_data
    
    # Execute
    target_date = (datetime.datetime.now() + datetime.timedelta(days=1)).strftime('%Y-%m-%d')
    result = get_prediction_for_date(target_date)
    
    # Verify
    # 1. WeatherService was called with correct args
    mock_fetch.assert_called_once()
    
    # 2. Result source indicates it used the mock
    # The source string is usually constructed in predict_future as: meta.get('source') + " (ML/Heuristic)"
    assert "mocked_service" in result['source']
    
    print("\n✅ Mock Weather Test Passed!")
    print(f"Source Trace: {result['source']}")
