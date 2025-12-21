import geocoder
from datetime import datetime
import zoneinfo

def get_location_from_ip():
    """ Gets approximate user location from the user IP address."""
    try:
        import requests
        resp = requests.get('https://ipinfo.io/json', timeout=3)
        if resp.status_code == 200:
            data = resp.json()
            loc = data.get('loc', '').split(',')
            if len(loc) == 2:
                return [float(loc[0]), float(loc[1])], f"{data.get('city')}, {data.get('region')}"
    except Exception as e:
        print(f"Geocoding Error: {e}")
    return None, None
    
def get_local_timezone():
    """Gets the system's local timezone."""
    try:
        # Preferred method (Python 3.9+): use zoneinfo
        return zoneinfo.ZoneInfo(datetime.now().astimezone().tzinfo.key)
    except (ImportError, AttributeError):
        try:
            # Fallback for older Python versions or systems without zoneinfo
            import tzlocal
            return tzlocal.get_localzone()
        except ImportError:
            # Last resort: return None if tzlocal is not available
            print("Warning: tzlocal library not found.")
            return None
