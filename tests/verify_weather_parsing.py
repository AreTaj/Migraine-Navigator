
import unittest
from unittest.mock import MagicMock, patch
from datetime import datetime, timedelta
import pandas as pd
import sys
import os

# Add project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from services.weather_service import WeatherService

class TestWeatherParsing(unittest.TestCase):
    def test_pres_change_calculation(self):
        # Mock Response
        # Today: 1010 hPa
        # Tomorrow: 1000 hPa (Storm coming!)
        mock_data = {
            "weather": [
                {
                    "date": "2025-12-16",
                    "avgtempC": "20",
                    "mintempC": "15",
                    "maxtempC": "25",
                    "sunHour": "10",
                    "hourly": [{"pressure": "1010", "humidity": "50", "tempC": "20"}] * 8 # Constant day
                },
                {
                    "date": "2025-12-17",
                    "avgtempC": "15",
                    "mintempC": "10",
                    "maxtempC": "20",
                    "sunHour": "10",
                    "hourly": [{"pressure": "1000", "humidity": "60", "tempC": "15"}] * 8 # Constant day
                }
            ]
        }
        
        # Test Case 1: Predict for Tomorrow (2025-12-17)
        # Prev Day is 2025-12-16 (Available)
        # Expected Change: 1000 - 1010 = -10.0
        
        target_date = datetime(2025, 12, 17)
        
        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_data
            mock_resp.raise_for_status.return_value = None
            mock_get.return_value = mock_resp
            
            result = WeatherService.fetch_forecast(40.7, -74.0, target_date)
            
            print(f"\nTarget: {target_date.date()}")
            print(f"Result Pres: {result['pres']}")
            print(f"Result Pres Change: {result['pres_change']}")
            
            self.assertEqual(result['pres'], 1000.0)
            self.assertEqual(result['pres_change'], -10.0)
            
    def test_missing_prev_day(self):
        # Test Case 2: Predict for Today (2025-12-16)
        # Prev Day is 2025-12-15 (Missing from list)
        # Expected Change: 0.0 (Fallback)
        
        mock_data = {
            "weather": [
                {
                    "date": "2025-12-16",
                    "hourly": [{"pressure": "1010", "humidity": "50", "tempC": "20"}]
                }
            ]
        }
        
        target_date = datetime(2025, 12, 16)
        
        with patch('requests.get') as mock_get:
            mock_resp = MagicMock()
            mock_resp.json.return_value = mock_data
            mock_get.return_value = mock_resp
            
            result = WeatherService.fetch_forecast(40.7, -74.0, target_date)
            
            print(f"\nTarget: {target_date.date()} (No History)")
            print(f"Result Pres Change: {result['pres_change']}")
            
            self.assertEqual(result['pres_change'], 0.0)

if __name__ == '__main__':
    unittest.main()
