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
