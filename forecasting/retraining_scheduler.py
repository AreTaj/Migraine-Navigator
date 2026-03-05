"""
retraining_scheduler.py — Issue #52
Provides helpers for user-initiated, threshold-based model retraining.

Public API:
  get_entries_since_last_training(db_path) -> int
  run_training_safely(db_path) -> bool
  enqueue_training(db_path)
"""

import glob
import os
import sqlite3
import threading
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

# ─── Paths ────────────────────────────────────────────────────────────────────
from api.utils import get_data_dir
_MODEL_DIR = os.path.join(get_data_dir(), 'models')
os.makedirs(_MODEL_DIR, exist_ok=True)

# ─── Concurrency guard ────────────────────────────────────────────────────────
_training_lock = threading.Lock()
_is_training = False  # Readable by the status endpoint without acquiring lock


def _get_latest_model_mtime() -> float | None:
    """
    Return the modification time of the most-recently-saved classifier .pkl,
    or None if no model files exist yet.
    """
    pattern = os.path.join(_MODEL_DIR, 'best_model_clf_*.pkl')
    files = sorted(glob.glob(pattern), reverse=True)
    if not files:
        return None
    return os.path.getmtime(files[0])


def get_entries_since_last_training(db_path: str) -> int:
    """
    Count migraine_log rows added after the last successful training run.

    - If no model exists, returns the total number of rows (all data is
      "new" from the model's perspective).
    - If a model exists, returns rows whose Date is strictly after the
      model's mtime converted to a YYYY-MM-DD string.
    """
    mtime = _get_latest_model_mtime()

    try:
        conn = sqlite3.connect(db_path)
        if mtime is None:
            # No model at all — every row is effectively unlearned
            count = conn.execute("SELECT COUNT(*) FROM migraine_log").fetchone()[0]
        else:
            # Convert unix mtime to date string for comparison
            cutoff = datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')
            count = conn.execute(
                "SELECT COUNT(*) FROM migraine_log WHERE Date > ?",
                (cutoff,)
            ).fetchone()[0]
        conn.close()
        return count
    except Exception as e:
        logger.warning(f"Could not determine entries since last training: {e}")
        return 0


def get_last_trained_date() -> str | None:
    """
    Return the last-trained date as a YYYY-MM-DD string, derived from
    the mtime of the most recent classifier file. Returns None if no model.
    """
    mtime = _get_latest_model_mtime()
    if mtime is None:
        return None
    return datetime.fromtimestamp(mtime).strftime('%Y-%m-%d')


def run_training_safely(db_path: str) -> bool:
    """
    Thread-safe wrapper around train_and_evaluate().

    - Acquires the training lock (non-blocking); skips if already training.
    - Catches all exceptions so a failed train never propagates to callers.
    - Returns True on success, False if skipped or failed.
    """
    global _is_training

    acquired = _training_lock.acquire(blocking=False)
    if not acquired:
        logger.info("Training already in progress; skipping duplicate request.")
        return False

    _is_training = True
    try:
        logger.info(f"Starting background model training against {db_path}...")
        from forecasting.train_model import train_and_evaluate
        from forecasting.inference import clear_prediction_cache
        train_and_evaluate(db_path=db_path)
        clear_prediction_cache()
        logger.info("Background model training completed successfully and prediction cache cleared.")
        return True
    except Exception as e:
        logger.error(f"Background training failed: {e}", exc_info=True)
        return False
    finally:
        _is_training = False
        _training_lock.release()


def enqueue_training(db_path: str) -> None:
    """
    Fire-and-forget: spawn a daemon thread to run training.
    Returns immediately so the HTTP response is not blocked.
    """
    t = threading.Thread(
        target=run_training_safely,
        args=(db_path,),
        daemon=True,
        name="retraining-worker"
    )
    t.start()
    logger.info("Retraining worker thread started.")


def is_training_in_progress() -> bool:
    """Return True if a training run is currently active."""
    return _is_training
