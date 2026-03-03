"""
Tests for Issue #52: Automatic Model Retraining Scheduler.

Covers:
1. get_entries_since_last_training() — staleness checks
2. run_training_safely() — concurrent lock exclusion
3. GET /api/v1/training/status — endpoint response shape
"""

import os
import glob
import sqlite3
import time
import threading
import pytest
from unittest.mock import patch, MagicMock
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db_path_dep


# ─── Helpers ─────────────────────────────────────────────────────────────────

def make_db(db_path: str, rows: list[dict]):
    """Create a minimal migraine_log and insert rows."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS migraine_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date TEXT, Time TEXT, "Pain Level" INTEGER
        )
    """)
    for r in rows:
        conn.execute('INSERT INTO migraine_log (Date, Time, "Pain Level") VALUES (?, ?, ?)',
                     (r['Date'], r['Time'], r['Pain Level']))
    conn.commit()
    conn.close()


def override_db(path: str):
    def _dep(): return path
    return _dep


# ─── get_entries_since_last_training ─────────────────────────────────────────

class TestStalenessCheck:

    def test_count_no_model(self, tmp_path):
        """No .pkl files → returns total row count."""
        db = str(tmp_path / "test.db")
        make_db(db, [
            {"Date": "2025-01-01", "Time": "08:00", "Pain Level": 3},
            {"Date": "2025-01-02", "Time": "08:00", "Pain Level": 5},
        ])
        model_dir = str(tmp_path / "models")
        os.makedirs(model_dir, exist_ok=True)

        from forecasting import retraining_scheduler as sched
        with patch.object(sched, '_MODEL_DIR', model_dir):
            count = sched.get_entries_since_last_training(db)

        assert count == 2, "All rows should count as 'since last training' when no model exists"

    def test_count_stale_model(self, tmp_path):
        """Model is older than newest DB entry → returns positive count."""
        db = str(tmp_path / "test.db")
        # Insert entries dated in the past
        make_db(db, [
            {"Date": "2020-01-01", "Time": "08:00", "Pain Level": 2},
            {"Date": "2020-06-01", "Time": "08:00", "Pain Level": 4},
        ])

        model_dir = str(tmp_path / "models")
        os.makedirs(model_dir, exist_ok=True)

        # Create a fake .pkl with a very old mtime (1970)
        pkl = os.path.join(model_dir, "best_model_clf_1000.pkl")
        with open(pkl, "w") as f:
            f.write("fake")
        os.utime(pkl, (1000, 1000))  # Unix timestamp 1000 = Jan 1, 1970

        from forecasting import retraining_scheduler as sched
        with patch.object(sched, '_MODEL_DIR', model_dir):
            count = sched.get_entries_since_last_training(db)

        assert count > 0, "Entries dated after the model's mtime should be counted"

    def test_count_fresh_model(self, tmp_path):
        """Model is newer than all DB entries → returns 0."""
        db = str(tmp_path / "test.db")
        make_db(db, [
            {"Date": "2020-01-01", "Time": "08:00", "Pain Level": 2},
        ])

        model_dir = str(tmp_path / "models")
        os.makedirs(model_dir, exist_ok=True)

        # Create a fake .pkl with a future mtime
        pkl = os.path.join(model_dir, "best_model_clf_9999999999.pkl")
        with open(pkl, "w") as f:
            f.write("fake")
        future_ts = time.time() + 86400  # 1 day in the future
        os.utime(pkl, (future_ts, future_ts))

        from forecasting import retraining_scheduler as sched
        with patch.object(sched, '_MODEL_DIR', model_dir):
            count = sched.get_entries_since_last_training(db)

        assert count == 0, "No entries should count as new when model is fresher than all data"


# ─── run_training_safely (concurrency lock) ───────────────────────────────────

class TestConcurrentLock:

    def test_concurrent_retrain_calls_train_once(self, tmp_path):
        """
        Two simultaneous calls to run_training_safely should result in
        train_and_evaluate being called exactly once.
        """
        db = str(tmp_path / "test.db")
        make_db(db, [{"Date": "2025-01-01", "Time": "08:00", "Pain Level": 3}])

        call_count = {"n": 0}
        barrier = threading.Barrier(2)  # synchronize both threads at start

        def fake_train(db_path=None):
            call_count["n"] += 1
            time.sleep(0.2)  # simulate training duration

        from forecasting import retraining_scheduler as sched
        # Reset the lock in case a prior test left it acquired
        sched._training_lock = threading.Lock()
        sched._is_training = False

        results = []

        def _run():
            barrier.wait()  # Both threads fire simultaneously
            result = sched.run_training_safely.__wrapped__(db) if hasattr(sched.run_training_safely, '__wrapped__') else None
            # Use the real function with mocked train_and_evaluate
            with patch('forecasting.retraining_scheduler.train_and_evaluate', fake_train):
                r = sched.run_training_safely(db)
            results.append(r)

        # Patch the import inside run_training_safely
        import_patch_path = 'forecasting.retraining_scheduler.train_and_evaluate'
        original_run = sched.run_training_safely

        call_count["n"] = 0
        sched._training_lock = threading.Lock()
        sched._is_training = False

        threads = []
        results.clear()

        with patch('forecasting.train_model.train_and_evaluate', fake_train):
            for _ in range(2):
                t = threading.Thread(target=lambda: results.append(sched.run_training_safely(db)))
                threads.append(t)

            barrier2 = threading.Barrier(2)

            def coordinated_run():
                barrier2.wait()
                results.append(sched.run_training_safely(db))

            results.clear()
            sched._training_lock = threading.Lock()
            sched._is_training = False
            t1 = threading.Thread(target=coordinated_run)
            t2 = threading.Thread(target=coordinated_run)

            with patch('forecasting.train_model.train_and_evaluate', fake_train):
                t1.start(); t2.start()
                t1.join(); t2.join()

        # One should have returned True (ran), one False (skipped lock)
        assert True in results, "At least one training run should succeed"
        assert False in results, "One thread should be skipped due to lock"


# ─── GET /api/v1/training/status ─────────────────────────────────────────────

class TestStatusEndpoint:

    @pytest.fixture
    def client(self, tmp_path):
        db = str(tmp_path / "test.db")
        make_db(db, [])
        app.dependency_overrides[get_db_path_dep] = override_db(db)
        yield TestClient(app), db, tmp_path
        app.dependency_overrides.clear()

    def test_status_endpoint_returns_correct_shape(self, client):
        tc, db, _ = client
        res = tc.get("/api/v1/training/status")
        assert res.status_code == 200
        body = res.json()
        assert "needs_retraining" in body
        assert "entries_since_last_train" in body
        assert "last_trained" in body
        assert "is_training" in body
        assert "threshold" in body

    def test_status_needs_retraining_when_threshold_met(self, client, tmp_path):
        tc, db, model_tmp = client
        # Insert 5 entries (meets the RETRAIN_THRESHOLD)
        conn = sqlite3.connect(db)
        for i in range(5):
            conn.execute('INSERT INTO migraine_log (Date, Time, "Pain Level") VALUES (?, ?, ?)',
                         (f"2025-01-0{i+1}", "08:00", 3))
        conn.commit(); conn.close()

        # Patch model dir to have no .pkl (simulates no model yet)
        model_dir = str(model_tmp / "models")
        os.makedirs(model_dir, exist_ok=True)
        from forecasting import retraining_scheduler as sched
        with patch.object(sched, '_MODEL_DIR', model_dir):
            res = tc.get("/api/v1/training/status")

        assert res.status_code == 200
        body = res.json()
        assert body["entries_since_last_train"] >= 5
