import unittest
from unittest.mock import patch, MagicMock
import os
import pandas as pd
import sys

# Add the top-level directory to sys.path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from weather.weather import fetch_weather_data, get_historical_weather, save_weather_data_to_csv

class TestWeather(unittest.TestCase):
    def setUp(self):
        # Create a temporary CSV file for migraine log
        self.migraine_log_file = "test_migraine_log.csv"
        with open(self.migraine_log_file, 'w') as f:
            f.write("Date,Latitude,Longitude\n")
            f.write("2023-10-10,40.7128,-74.0060\n")

        # Create a temporary CSV file for weather data
        self.weather_data_file = "test_weather_data.csv"
        with open(self.weather_data_file, 'w') as f:
            f.write("date,tavg,tmin,tmax,pres,prcp,wspd,tsun,average_humidity,midday_humidity,Latitude,Longitude\n")

    def tearDown(self):
        if os.path.exists(self.migraine_log_file):
            os.remove(self.migraine_log_file)
        if os.path.exists(self.weather_data_file):
            os.remove(self.weather_data_file)

    @patch('weather.weather.get_historical_weather')
    def test_fetch_weather_data(self, mock_get_historical_weather):
        # Mock get_historical_weather to return sample data
        mock_get_historical_weather.return_value = [{
            'date': '2023-10-10',
            'tavg': 15.0,
            'tmin': 10.0,
            'tmax': 20.0,
            'pres': 1015.0,
            'prcp': 0.0,
            'wspd': 5.0,
            'tsun': 300.0,
            'average_humidity': 70.0,
            'midday_humidity': 60.0,
            'Latitude': 40.7128,
            'Longitude': -74.0060,
            'key': ('2023-10-10', 40.7128, -74.0060)  # Include the key field
        }]

        fetch_weather_data(migraine_log_file=self.migraine_log_file, weather_data_file=self.weather_data_file)

        # Check if the weather data file was updated
        with open(self.weather_data_file, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 1)  # Header + 1 data line

    def test_save_weather_data_to_csv(self):
        weather_data = [{
            'date': '2023-10-10',
            'tavg': 15.0,
            'tmin': 10.0,
            'tmax': 20.0,
            'pres': 1015.0,
            'prcp': 0.0,
            'wspd': 5.0,
            'tsun': 300.0,
            'average_humidity': 70.0,
            'midday_humidity': 60.0,
            'Latitude': 40.7128,
            'Longitude': -74.0060,
            'key': ('2023-10-10', 40.7128, -74.0060)  # Include the key field
        }]

        save_weather_data_to_csv(weather_data, filename=self.weather_data_file)

        # Check if the weather data file was created and contains the correct data
        with open(self.weather_data_file, 'r') as f:
            lines = f.readlines()
            self.assertEqual(len(lines), 2)  # Header + 1 data line

if __name__ == '__main__':
    unittest.main()