import unittest
from unittest.mock import patch, MagicMock
import sys
import os
import sqlite3

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forecasting import inference

class TestForceHeuristic(unittest.TestCase):
    
    @patch('sqlite3.connect')
    @patch('forecasting.inference.load_models')
    @patch('forecasting.inference.FeatureEngine.construct_features')
    @patch('forecasting.inference.get_recent_history')
    @patch('forecasting.inference.get_latest_location_from_db')
    @patch('forecasting.inference.WeatherService')  # Mock the class in inference module
    def test_force_heuristic_bypasses_ml(self, mock_weather_cls, mock_loc, mock_history, mock_features, mock_load_models, mock_connect):
        # Setup Mocks
        mock_loc.return_value = (34.05, -118.25)
        # Weather mock
        mock_weather_cls.fetch_forecast.return_value = {'source': 'live'}
        
        # Feature Engine Mock
        mock_features.return_value = (MagicMock(), {'source': 'live'})
        
        # DB Mock to return force_heuristic_mode=True
        mock_conn = MagicMock()
        mock_cursor = MagicMock()
        # The query is: SELECT value FROM user_settings WHERE key='force_heuristic_mode'
        # We need to ensure it returns 'true' when asked for that key.
        
        # Because connect is called multiple times (once for check, once inside fallback), 
        # we need to be careful. The first call is the check.
        mock_connect.return_value = mock_conn
        mock_conn.cursor.return_value = mock_cursor
        
        # Mock fetchone to return 'true'
        mock_cursor.fetchone.return_value = ('true',)
        
        # Execute
        result = inference.get_prediction_for_date("2026-01-01")
        
        # Assertions
        # 1. load_models should NOT be called
        mock_load_models.assert_not_called()
        
        # 2. Result source should indicate Heuristic
        self.assertIn("(Heuristic)", result['source'])
        print(f"\n[Verification] Force Mode Result Source: {result['source']}")

if __name__ == '__main__':
    unittest.main()
