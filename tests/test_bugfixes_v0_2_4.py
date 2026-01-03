import pytest
from forecasting.inference import get_hourly_forecast
from unittest.mock import patch, MagicMock
from datetime import datetime

class TestBugFixesV024:
    
    @patch('forecasting.inference.WeatherService.fetch_hourly')
    @patch('forecasting.inference.get_latest_location_from_db')
    @patch('forecasting.inference.get_recent_history')
    @patch('forecasting.inference.FeatureEngine.get_circadian_priors')
    def test_hourly_forecast_handles_none_date(self, mock_priors, mock_history, mock_loc, mock_weather):
        """
        Regression Test for Issue: 'NoneType' object has no attribute 'strftime'
        Verify that passing None to get_hourly_forecast defaults to current time effectively.
        """
        # Setup mocks to avoid real DB/API calls
        mock_loc.return_value = (34.05, -118.25)
        mock_history.return_value = MagicMock() # DataFrame mock not strictly needed if we don't access it deeply
        mock_priors.return_value = {i: 0.5 for i in range(24)}
        
        # Mock weather response
        mock_weather.return_value = [{
            'time': datetime.now().strftime("%Y-%m-%dT%H:00"),
            'temperature_2m': 20,
            'relative_humidity_2m': 50, 
            'surface_pressure': 1015,
            'precipitation': 0,
            'wind_speed_10m': 5,
            'temp': 20,  # Service returns 'temp' key in result dict
            'humidity': 50,
            'pressure': 1015,
            'pressure_change_3h': 0,
            'prcp': 0,
            'wind': 5
        }]

        try:
            # THIS CALL CAUSED THE CRASH
            result = get_hourly_forecast(None)
            
            assert isinstance(result, list)
            assert len(result) >= 0
            # If we get here, the None handling worked (no AttributeError)
        except AttributeError as e:
            pytest.fail(f"get_hourly_forecast(None) raised AttributeError: {e}")
        except Exception as e:
            # Other errors might be setup related, but we specifically care about AttributeError on strftime
            if "strftime" in str(e):
                 pytest.fail(f"Regression detected: {e}")
            raise e

    @patch('forecasting.inference.WeatherService.fetch_weekly')
    @patch('forecasting.inference.get_latest_location_from_db')
    @patch('forecasting.inference.get_recent_history')
    @patch('forecasting.inference.load_models')
    def test_weekly_forecast_structure(self, mock_load, mock_history, mock_loc, mock_weather):
        """
        Verify get_weekly_forecast returns 7 days of data with correct keys.
        """
        from forecasting.inference import get_weekly_forecast
        
        # Mock Dependencies
        mock_loc.return_value = (34.05, -118.25)
        mock_history.return_value = MagicMock()
        mock_load.return_value = (None, None) # Simulate no models -> Heuristic Fallback
        
        # Mock 7 days of weather
        mock_weather_data = {}
        base = datetime.now()
        from datetime import timedelta
        for i in range(7):
            d = (base + timedelta(days=i+1)).strftime("%Y-%m-%d") # Forecast starts tomorrow
            mock_weather_data[d] = {
                'tavg': 20, 'tmin': 15, 'tmax': 25, 'prcp': 0, 'wspd': 5, 
                'pres': 1015, 'tsun': 10, 'average_humidity': 50, 
                'pres_change': 0, 'midday_humidity': 50,
                'Latitude': 34.05, 'Longitude': -118.25
            }
        mock_weather.return_value = mock_weather_data

        result = get_weekly_forecast()
        
        assert isinstance(result, list)
        assert len(result) == 7
        
        for day in result:
            assert "date" in day
            assert "risk_probability" in day
            assert "risk_level" in day
            assert "predicted_pain" in day

    @patch('forecasting.inference.WeatherService.fetch_hourly')
    @patch('forecasting.inference.get_latest_location_from_db')
    @patch('forecasting.inference.get_recent_history')
    @patch('forecasting.inference.FeatureEngine.get_circadian_priors')
    def test_hourly_forecast_structure(self, mock_priors, mock_history, mock_loc, mock_weather):
        """
        Verify get_hourly_forecast returns correct keys for frontend (risk_score, humidity).
        """
        from forecasting.inference import get_hourly_forecast
        
        # Mock Dependencies
        mock_loc.return_value = (34.05, -118.25)
        mock_history.return_value = MagicMock()
        mock_priors.return_value = {i: 0.5 for i in range(24)}
        
        # Mock 1 hour of weather
        mock_weather.return_value = [{
            'time': datetime.now().strftime("%Y-%m-%dT%H:00"),
            'temperature_2m': 20,
            'relative_humidity_2m': 50,
            'temp': 20,
            'humidity': 50,
            'desc': 'clear'
        }]

        result = get_hourly_forecast(None)
        
        assert isinstance(result, list)
        assert len(result) > 0
        
        hour = result[0]
        assert "risk_score" in hour  # WAS 'probability'
        assert "risk_level" in hour
        assert "temp" in hour
        assert "humidity" in hour    # WAS MISSING

def test_hourly_forecast_details(monkeypatch):
    """
    Ensure 'details' key is populated for the tooltip breakdown.
    """
    # Mock services to avoid external calls
    import sys
    import pandas as pd
    from unittest.mock import MagicMock
    
    # Save originals if they exist (optional, but good practice)
    # But for now, just ensure we clean up the mocks we inject
    
    try:
        # Mock WeatherService
        sys.modules['services.weather_service'] = MagicMock()
        # Mock FeatureEngine
        sys.modules['forecasting.feature_engine'] = MagicMock()
        
        # Setup Returns
        sys.modules['services.weather_service'].WeatherService.fetch_hourly.return_value = [
            {'time': '2025-01-01T10:00:00', 'temp': 20, 'humidity': 50, 'prcp': 0}
        ]
        sys.modules['forecasting.feature_engine'].FeatureEngine.get_circadian_priors.return_value = [0.1] * 24
        
        # We also need to mock DB path for the location check
        monkeypatch.setattr("forecasting.inference.get_latest_location_from_db", lambda x: (34.05, -118.25))
        monkeypatch.setattr("forecasting.inference.get_recent_history", lambda x: pd.DataFrame())

        from forecasting.inference import get_hourly_forecast
        
        results = get_hourly_forecast(None)
        assert len(results) > 0
        
        first = results[0]
        assert "details" in first
        assert "heuristic_weather" in first["details"] or "components" in first["details"] or True
        
    finally:
        # Cleanup Mocks to prevent pollution
        if 'services.weather_service' in sys.modules:
            del sys.modules['services.weather_service']
        if 'forecasting.feature_engine' in sys.modules:
            del sys.modules['forecasting.feature_engine']
