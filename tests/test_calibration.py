
import unittest
from unittest.mock import patch, MagicMock
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from forecasting import inference

class TestCalibration(unittest.TestCase):
    
    @patch('forecasting.inference.get_prediction_for_date')
    @patch('forecasting.heuristic_predictor.HeuristicPredictor')
    @patch('forecasting.inference.WeatherService')
    # It seems get_circadian_priors is imported from feature_engine in inference.py?
    # Or maybe it is not imported at module level?
    # I will patch where it is defined: forecasting.feature_engine.FeatureEngine.get_circadian_priors
    @patch('forecasting.feature_engine.FeatureEngine.get_circadian_priors')
    @patch('forecasting.inference.get_latest_location_from_db')
    def test_truth_propagation(self, mock_loc, mock_priors, mock_weather_cls, mock_heuristic_cls, mock_daily_pred):
        # Setup Mocks
        mock_loc.return_value = (34.05, -118.25)
        mock_priors.return_value = [0.1] * 24
        
        # Mock Weather for 24h
        mock_weather_cls.fetch_hourly.return_value = [{'time': f'2025-01-01T{i:02d}:00:00', 'temp': 20, 'humidity': 50} for i in range(24)]
        
        # Mock Heuristic Predictor (Low Risk)
        mock_predictor = MagicMock()
        mock_predictor.predict_hourly.return_value = {
            'probability': 0.2, # 20% Raw Risk
            'risk_level': 'Low',
            'components': {}
        }
        mock_heuristic_cls.return_value = mock_predictor
        
        # Mock Daily Prediction (High Risk - The Truth)
        mock_daily_pred.return_value = {
            'probability': 80.0, # 80% Daily Risk
            'risk_level': 'High'
        }
        
        # Execute
        results = inference.get_hourly_forecast("2025-01-01")
        
        # Assertions
        # 1. Check if results are scaled
        # Peak Heuristic = 20.0
        # Daily Truth = 80.0
        # Scaling Factor = 80 / 20 = 4.0 -> Capped at 2.5
        # Expected Result = 20 * 2.5 = 50.0%
        
        first_hour = results[0]
        self.assertEqual(first_hour['risk_score'], 50.0) 
        self.assertEqual(first_hour['risk_level'], 'Moderate') # 50% is Moderate
        
        print(f"\n[Verification] Raw: 20%, Daily: 80%, Scaled: {first_hour['risk_score']}%")

if __name__ == '__main__':
    unittest.main()
