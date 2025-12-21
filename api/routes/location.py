from fastapi import APIRouter, HTTPException
import geocoder

router = APIRouter()

@router.get("/location", tags=["Location"])
async def get_current_location():
    """
    Get approximate location based on IP address.
    Returns:
        dict: {
            "latitude": float,
            "longitude": float,
            "city": str,
            "state": str,
            "country": str,
            "address": str
        }
    """
    try:
        import requests
        # Use ipinfo.io (free tier, 50k requests/month, reliable)
        # Bundled certifi will handle SSL automatically via environment vars
        resp = requests.get('https://ipinfo.io/json', timeout=5)
        resp.raise_for_status()
        data = resp.json()
        
        loc_str = data.get('loc', '').split(',')
        lat = float(loc_str[0]) if len(loc_str) == 2 else None
        lng = float(loc_str[1]) if len(loc_str) == 2 else None
        
        return {
            "latitude": lat,
            "longitude": lng,
            "city": data.get('city'),
            "state": data.get('region'), # Region is usually state
            "country": data.get('country'),
            "address": f"{data.get('city')}, {data.get('region')}"
        }
    except Exception as e:
        print(f"Location Error: {e}")
        # Return fallback or raise
        raise HTTPException(status_code=500, detail=f"Failed to get location from IP: {str(e)}")
