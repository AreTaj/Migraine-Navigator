from meteostat import Point, Daily, Hourly
import pandas as pd
import csv
import os

# Ignore FutureWarnings
#warnings.simplefilter(action='ignore', category=FutureWarning)

# Define the filename variable
weather_data_filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'weather_data.csv')
migraine_data_filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'migraine_log.csv')
combined_data_filename = os.path.join(os.path.dirname(__file__), '..', 'data', 'combined_data.csv')

def get_hourly_weather(lat, lon, date):
    """Fetches hourly weather data, handles missing data gracefully."""
    try:
        location = Point(lat, lon)
        date_obj = pd.to_datetime(date)
        start = date_obj
        end = date_obj + pd.Timedelta(days=1)
        data = Hourly(location, start, end)
        data = data.fetch()
        return data
    except Exception as e:
        print(f"Error fetching hourly data for {date}: {e}")
        return pd.DataFrame()
    
def get_daily_humidity(lat, lon, date):
    """Gets average and midday humidity, handles missing data robustly."""
    hourly_data = get_hourly_weather(lat, lon, date)
    humidity_info = {"average_humidity": None, "midday_humidity": None}  # Initialize

    if not hourly_data.empty and 'rhum' in hourly_data.columns:
        humidity_info["average_humidity"] = hourly_data['rhum'].mean()
        try:
            midday_humidity = hourly_data.loc[hourly_data.index.hour == 12, 'rhum'].iloc[0]
            humidity_info["midday_humidity"] = midday_humidity
        except IndexError:
            print(f"Warning: No midday humidity data for {date}.")

    elif not hourly_data.empty:
        print(f"Warning: No 'rhum' data in hourly data for {date}.")
    else:
        print(f"Warning: No hourly data available for {date}.")
    return humidity_info
    
def get_historical_weather(lat, lon, start_date, end_date):
    # Define the location and date range
    location = Point(lat, lon)
    start = pd.to_datetime(start_date)
    end = pd.to_datetime(end_date)
    dates = pd.date_range(start, end)
    all_weather_data = []

    for date in dates:
        daily_data = Daily(location, date, date).fetch()
        humidity_info = get_daily_humidity(lat, lon, date)

        weather_info = {"date": date.strftime('%Y-%m-%d'), "Latitude": lat, "Longitude": lon}
        if not daily_data.empty:
            for col in ['tavg', 'tmin', 'tmax', 'pres', 'prcp', 'wspd', 'tsun']:
                weather_info[col] = daily_data[col].iloc[0] if col in daily_data else None
        else:
            print(f"Warning: No daily data available for {date}.")
            for col in ['tavg', 'tmin', 'tmax', 'pres', 'prcp', 'wspd', 'tsun']:
                weather_info[col] = None
        weather_info.update(humidity_info)
        all_weather_data.append(weather_info)

    return all_weather_data

def save_weather_data_to_csv(weather_data, filename=weather_data_filename):
    fieldnames = ['date', 'tavg', 'tmin', 'tmax', 'pres', 'prcp', 'wspd', 'tsun', 'average_humidity', 'midday_humidity', 'Latitude', 'Longitude']
    with open(filename, 'w', newline='') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        for data in weather_data:
            # Remove the 'key' field before writing
            del data['key']
            writer.writerow(data)

def fetch_weather_data(migraine_log_file=migraine_data_filename, weather_data_file=weather_data_filename):
    migraine_data = pd.read_csv(migraine_log_file)
    # Ensure correct data types for comparisons
    migraine_data['Date'] = pd.to_datetime(migraine_data['Date'])

    # Create keys for migraine data
    migraine_data['key'] = migraine_data.apply(lambda row: (row['Date'], row['Latitude'], row['Longitude']), axis=1)

    data_path = os.path.join(os.path.dirname(__file__), '..', 'data', weather_data_file)

    # Load existing weather data
    try:
        existing_weather_data = pd.read_csv(data_path) # Parse dates in existing data
        existing_weather_data['date'] = pd.to_datetime(existing_weather_data['date'], format='mixed') #Parse date after reading csv
        #existing_weather_data = pd.read_csv(data_path, parse_dates=['date'])   # this line may raise FutureWarning
        # Check if 'Latitude' and 'Longitude' columns exist before creating the key column
        if not existing_weather_data.empty and 'Latitude' in existing_weather_data.columns and 'Longitude' in existing_weather_data.columns:
            existing_weather_data['key'] = existing_weather_data.apply(lambda row: (row['date'], row['Latitude'], row['Longitude']), axis=1)
        else:
            existing_weather_data['key'] = pd.Series(dtype='object')  # Create empty series of correct type
    except FileNotFoundError:
        existing_weather_data = pd.DataFrame(columns=['date', 'tavg', 'tmin', 'tmax', 'pres', 'prcp', 'wspd', 'tsun', 'average_humidity', 'midday_humidity', 'Latitude', 'Longitude'])
        print("Weather data file not found. Creating a new one.")
        existing_weather_data['key'] = pd.Series(dtype='object') #Create empty series of correct type

    # Identify missing entries (using keys)
    missing_entries = migraine_data[~migraine_data['key'].isin(existing_weather_data['key'])]

    all_weather_data = []
    if not missing_entries.empty:
        for _, row in missing_entries.iterrows():
            lat = row['Latitude']
            lon = row['Longitude']
            date = row['Date']
            weather_data = get_historical_weather(lat, lon, date, date)
            all_weather_data.extend(weather_data)

        for i, data in enumerate(all_weather_data):
            data['Latitude'] = data.get('Latitude')
            data['Longitude'] = data.get('Longitude')

        if all_weather_data:
            combined_weather_data = pd.concat([existing_weather_data, pd.DataFrame(all_weather_data)], ignore_index=True)
            save_weather_data_to_csv(combined_weather_data.to_dict('records'), data_path)
        else:
            print("No weather data to add.")
    else:
        print("No new data to fetch")
            
# Do the thing
#fetch_weather_data()