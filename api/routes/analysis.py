from fastapi import APIRouter, HTTPException
from services.analysis_service import AnalysisService
import os

router = APIRouter()

from api.utils import get_db_path

@router.get("/analysis/summary")
def get_analysis_summary():
    try:
        stats = AnalysisService.get_analysis_data(get_db_path())
        if stats is None:
             return {"message": "No data available for analysis"}
        return stats
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/analysis/trends")
def get_migraine_trends(range: str = '1y'):
    """
    Get aggregated trends data for charts.
    range: '1m', '1y', 'all'
    """
    try:
        stats = AnalysisService.get_trends_data(get_db_path(), range_type=range)
        return stats
    except Exception as e:
        print(f"Trends Error: {e}")
        return [] # Return empty list on error to prevent crash
