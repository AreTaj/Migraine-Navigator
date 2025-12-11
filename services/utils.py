import geocoder
from datetime import datetime
import zoneinfo

def get_location_from_ip():
    """ Gets approximate user location from the user IP address."""
    g = geocoder.ip('me')
    if g.ok:
        return g.latlng, g.address
    else:
        print(f"Geocoding Error: {g.status_code}, {g.reason}")
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
