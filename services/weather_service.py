import requests
import logging
from datetime import timedelta
from typing import Optional, Dict, List, Any

# Setup logger
logger = logging.getLogger("weather_service")

class WeatherService:
    BASE_URL = "https://api.open-meteo.com/v1/forecast"
    
    @staticmethod
    def fetch_forecast(lat: float, lon: float, target_date) -> Optional[Dict[str, Any]]:
        """
        Fetches weather from Open-Meteo for the specific date.
        Returns feature dictionary or None if failed.
        """
        try:
            # Open-Meteo API: Request weather for target date.
            # We need start_date = target - 1 day to calculate pressure change context from "yesterday".
            start_dt = target_date - timedelta(days=1)
            start_str = start_dt.strftime('%Y-%m-%d')
            target_str = target_date.strftime('%Y-%m-%d')
            
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": start_str,
                "end_date": target_str,
                "hourly": "temperature_2m,relative_humidity_2m,surface_pressure,precipitation,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,sunshine_duration",
                "timezone": "auto"
            }
            
            response = requests.get(WeatherService.BASE_URL, params=params, timeout=5)
            if response.status_code >= 400:
                logger.error(f"Open-Meteo Error: {response.text}")
            response.raise_for_status()
            data = response.json()
            
            daily = data.get('daily', {})
            hourly = data.get('hourly', {})
            
            # Index Logic
            times = hourly.get('time', [])
            target_hourly_idx = -1
            prev_hourly_idx = -1
            
            for i, t in enumerate(times):
                if t.startswith(target_str):
                    target_hourly_idx = i
                if t.startswith(start_str):
                    prev_hourly_idx = i
                    
            if target_hourly_idx == -1:
                return None
                
            # Target Day Hourly (24h)
            h_temps = hourly['temperature_2m'][target_hourly_idx : target_hourly_idx+24]
            h_hums = hourly['relative_humidity_2m'][target_hourly_idx : target_hourly_idx+24]
            h_pres = hourly['surface_pressure'][target_hourly_idx : target_hourly_idx+24]
            h_wspd = hourly['wind_speed_10m'][target_hourly_idx : target_hourly_idx+24]
            h_prcp = hourly['precipitation'][target_hourly_idx : target_hourly_idx+24]
            
            # Pressure Change (Target Avg - Previous Avg)
            pres_change = 0.0
            if prev_hourly_idx != -1:
                prev_pres_list = hourly['surface_pressure'][prev_hourly_idx : prev_hourly_idx+24]
                if len(prev_pres_list) >= 24 and h_pres: 
                    prev_avg_pres = sum(prev_pres_list) / len(prev_pres_list)
                    curr_avg_pres = sum(h_pres) / len(h_pres)
                    pres_change = curr_avg_pres - prev_avg_pres

            # Daily Aggregates
            daily_times = daily.get('time', [])
            d_idx = -1
            for i, t in enumerate(daily_times):
                if t == target_str:
                    d_idx = i
                    break
            
            if d_idx == -1:
                tmin = min(h_temps) if h_temps else 0
                tmax = max(h_temps) if h_temps else 0
                tsun = 0 
            else:
                tmin = daily['temperature_2m_min'][d_idx]
                tmax = daily['temperature_2m_max'][d_idx]
                tsun = (daily['sunshine_duration'][d_idx] or 0) / 60.0

            # Features Calculation
            tavg = sum(h_temps) / len(h_temps) if h_temps else 0
            pres = sum(h_pres) / len(h_pres) if h_pres else 1015.0
            humidity = sum(h_hums) / len(h_hums) if h_hums else 50.0
            wspd = sum(h_wspd) / len(h_wspd) if h_wspd else 0
            prcp = sum(h_prcp) if h_prcp else 0
            midday_humidity = h_hums[12] if len(h_hums) > 12 else humidity

            return {
                'id': -1,
                'tavg': tavg,
                'tmin': tmin,
                'tmax': tmax,
                'prcp': prcp,
                'wspd': wspd,
                'pres': pres,
                'tsun': tsun,
                'average_humidity': humidity,
                'pres_change': pres_change,
                'midday_humidity': midday_humidity
            }
            
        except Exception as e:
            logger.error(f"Weather API Error (Open-Meteo): {e}")
            return None

    @staticmethod
    def fetch_hourly(start_datetime, lat: float, lon: float, hours: int = 24) -> List[Dict[str, Any]]:
        """
        Fetches raw hourly weather for [start_datetime, start_datetime + hours].
        """
        try:
            start_str = start_datetime.strftime('%Y-%m-%d')
            end_dt = start_datetime + timedelta(hours=hours)
            end_str = (end_dt + timedelta(days=1)).strftime('%Y-%m-%d')
            req_start = (start_datetime - timedelta(days=1)).strftime('%Y-%m-%d')
            
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": req_start,
                "end_date": end_str,
                "hourly": "temperature_2m,relative_humidity_2m,surface_pressure,precipitation,wind_speed_10m",
                "timezone": "auto"
            }
            
            response = requests.get(WeatherService.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            hourly = data.get('hourly', {})
            times = hourly.get('time', [])
            result_hours = []
            
            target_iso_start = start_datetime.strftime('%Y-%m-%dT%H:00')
            start_idx = -1
            for i, t in enumerate(times):
                if t >= target_iso_start:
                    start_idx = i
                    break
                    
            if start_idx == -1: return []
            
            for i in range(start_idx, min(start_idx + hours, len(times))):
                pres_change_3h = 0.0
                if i >= 3:
                    curr_p = hourly['surface_pressure'][i] or 1015
                    prev_p = hourly['surface_pressure'][i-3] or 1015
                    pres_change_3h = curr_p - prev_p
                
                w_dict = {
                    'time': times[i],
                    'temp': hourly['temperature_2m'][i],
                    'humidity': hourly['relative_humidity_2m'][i],
                    'pressure': hourly['surface_pressure'][i],
                    'pressure_change_3h': pres_change_3h,
                    'prcp': hourly['precipitation'][i],
                    'wind': hourly['wind_speed_10m'][i]
                }
                result_hours.append(w_dict)
                
            return result_hours
            
        except Exception as e:
            logger.error(f"Hourly Weather Error: {e}")
            return []

    @staticmethod
    def fetch_weekly(start_date, lat: float, lon: float) -> Dict[str, Any]:
        """
        Fetches 7 days of weather starting from start_date in one API call.
        Returns a dict mapping date_str -> features.
        """
        try:
            real_start = start_date - timedelta(days=1)
            end_date = start_date + timedelta(days=6)
            
            params = {
                "latitude": lat,
                "longitude": lon,
                "start_date": real_start.strftime('%Y-%m-%d'),
                "end_date": end_date.strftime('%Y-%m-%d'),
                "hourly": "temperature_2m,relative_humidity_2m,surface_pressure,precipitation,wind_speed_10m",
                "daily": "temperature_2m_max,temperature_2m_min,sunshine_duration",
                "timezone": "auto"
            }
            
            response = requests.get(WeatherService.BASE_URL, params=params, timeout=5)
            response.raise_for_status()
            data = response.json()
            
            hourly = data.get('hourly', {})
            daily = data.get('daily', {})
            daily_map = {} 
            
            for i in range(7):
                target = start_date + timedelta(days=i)
                target_str = target.strftime('%Y-%m-%d')
                prev_str = (target - timedelta(days=1)).strftime('%Y-%m-%d')
                
                times = hourly.get('time', [])
                target_idx = -1
                prev_idx = -1
                for idx, t in enumerate(times):
                    if t.startswith(target_str): target_idx = idx
                    if t.startswith(prev_str): prev_idx = idx
                
                if target_idx == -1: continue 

                h_temps = hourly['temperature_2m'][target_idx : target_idx+24]
                h_hums = hourly['relative_humidity_2m'][target_idx : target_idx+24]
                h_pres = hourly['surface_pressure'][target_idx : target_idx+24]
                h_wspd = hourly['wind_speed_10m'][target_idx : target_idx+24]
                h_prcp = hourly['precipitation'][target_idx : target_idx+24]
                
                pres_change = 0.0
                if prev_idx != -1 and len(hourly['surface_pressure']) > prev_idx+24:
                    prev_list = hourly['surface_pressure'][prev_idx : prev_idx+24]
                    if prev_list and h_pres:
                        pres_change = (sum(h_pres)/len(h_pres)) - (sum(prev_list)/len(prev_list))

                d_times = daily.get('time', [])
                d_idx = -1
                for idx, t in enumerate(d_times):
                    if t == target_str: d_idx = idx
                
                tsun = 0
                tmin = min(h_temps) if h_temps else 0
                tmax = max(h_temps) if h_temps else 0
                
                if d_idx != -1:
                    tmin = daily['temperature_2m_min'][d_idx]
                    tmax = daily['temperature_2m_max'][d_idx]
                    tsun = (daily['sunshine_duration'][d_idx] or 0) / 60.0
                
                feat = {
                    'id': -1,
                    'tavg': sum(h_temps) / len(h_temps) if h_temps else 0,
                    'tmin': tmin,
                    'tmax': tmax,
                    'prcp': sum(h_prcp) if h_prcp else 0,
                    'wspd': sum(h_wspd) / len(h_wspd) if h_wspd else 0,
                    'pres': sum(h_pres) / len(h_pres) if h_pres else 1015,
                    'tsun': tsun,
                    'average_humidity': sum(h_hums) / len(h_hums) if h_hums else 50,
                    'pres_change': pres_change,
                    'midday_humidity': h_hums[12] if len(h_hums) > 12 else 50,
                    'Latitude': lat,
                    'Longitude': lon
                }
                daily_map[target_str] = feat
                
            return daily_map
            
        except Exception as e:
            logger.error(f"Batch Weather Error: {e}")
            return {}
