import requests

def get_historical_weather(city, date):
  api_key = "YOUR_API_KEY"
  url = f"https://api.openweathermap.org/data/2.5/history?q={city}&dt={date}&appid={api_key}"
  response = requests.get(url)
  data = response.json()
  # Extract relevant weather information from the JSON response
  return data

""" 
from meteostat import Point, Daily

# Define the location and date range
point = Point(37.7749, -122.4194)  # San Francisco
start = pd.Timestamp('2023-01-01')
end = pd.Timestamp('2023-01-31')

# Get daily data for the specified period
data = Daily(point, start, end)
data = data.fetch() """