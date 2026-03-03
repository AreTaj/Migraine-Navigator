"""
api/routes/training.py — Issue #52
Provides status check and user-initiated retrain endpoints.
"""

from fastapi import APIRouter, Depends
from api.dependencies import get_db_path_dep

router = APIRouter(prefix="/training", tags=["training"])

RETRAIN_THRESHOLD = 5  # Number of new entries that triggers the alert


@router.get("/status")
def training_status(db_path: str = Depends(get_db_path_dep)):
    """
    Returns whether the model needs retraining and how many new entries
    have been logged since the last training run.
    """
    from forecasting.retraining_scheduler import (
        get_entries_since_last_training,
        get_last_trained_date,
        is_training_in_progress,
    )

    entries_since = get_entries_since_last_training(db_path)
    last_trained = get_last_trained_date()

    return {
        "needs_retraining": entries_since >= RETRAIN_THRESHOLD,
        "entries_since_last_train": entries_since,
        "last_trained": last_trained,
        "is_training": is_training_in_progress(),
        "threshold": RETRAIN_THRESHOLD,
    }


@router.post("/retrain")
def trigger_retrain(db_path: str = Depends(get_db_path_dep)):
    """
    Enqueues a background training run and returns immediately.
    The frontend polls /status to learn when training completes.
    """
    from forecasting.retraining_scheduler import enqueue_training, is_training_in_progress

    if is_training_in_progress():
        return {"status": "already_running"}

    enqueue_training(db_path)
    return {"status": "queued"}
