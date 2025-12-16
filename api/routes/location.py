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
        # 'me' uses the current device's public IP
        g = geocoder.ip('me')
        
        if not g.ok:
            raise HTTPException(status_code=404, detail=f"Could not determine location: {g.reason}")
            
        return {
            "latitude": g.latlng[0] if g.latlng else None,
            "longitude": g.latlng[1] if g.latlng else None,
            "city": g.city,
            "state": g.state,
            "country": g.country,
            "address": g.address
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
