"""
Tests for Issue #50: Data Import System — Deduplication and Validation.

Tests exercise:
1. CSV import: duplicate rows (same Date+Time) are skipped.
2. CSV import: invalid Pain Level values are filtered out.
3. DB import: SQLite merge is based on (Date, Time), not id.
4. DB import: uses injected db_path, not hardcoded path.
"""

import sqlite3
import os
import io
import pytest
from fastapi.testclient import TestClient
from api.main import app
from api.dependencies import get_db_path_dep


def make_test_db(db_path: str, rows: list[dict]):
    """Helper: create a minimal migraine_log table and insert rows."""
    conn = sqlite3.connect(db_path)
    conn.execute("""
        CREATE TABLE IF NOT EXISTS migraine_log (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            Date TEXT,
            Time TEXT,
            "Pain Level" INTEGER,
            Medication TEXT,
            Dosage TEXT,
            Medications TEXT,
            Sleep TEXT,
            "Physical Activity" TEXT,
            Triggers TEXT,
            Notes TEXT,
            Location TEXT,
            Timezone TEXT,
            Latitude REAL,
            Longitude REAL
        )
    """)
    for row in rows:
        conn.execute(
            'INSERT INTO migraine_log (Date, Time, "Pain Level") VALUES (?, ?, ?)',
            (row['Date'], row['Time'], row['Pain Level'])
        )
    conn.commit()
    conn.close()


def override_db(path: str):
    """Return a FastAPI dependency override pointing to a specific DB."""
    def _override():
        return path
    return _override


@pytest.fixture
def client(tmp_path):
    """Test client with a fresh, empty test database."""
    db = str(tmp_path / "test.db")
    make_test_db(db, [])
    app.dependency_overrides[get_db_path_dep] = override_db(db)
    yield TestClient(app), db
    app.dependency_overrides.clear()


# ─── CSV Tests ────────────────────────────────────────────────────────────────

class TestCSVImport:

    def test_csv_imports_new_rows(self, client):
        tc, db = client
        csv_content = "Date,Time,Pain Level\n2025-01-01,08:00,5\n2025-01-02,09:00,3\n"
        res = tc.post("/api/v1/data/import/csv",
                      files={"file": ("data.csv", io.BytesIO(csv_content.encode()), "text/csv")})
        assert res.status_code == 200
        body = res.json()
        assert body["imported_rows"] == 2
        assert body["skipped_rows"] == 0

    def test_csv_deduplication_skips_existing_rows(self, client):
        tc, db = client
        # Seed the DB with one existing entry
        make_test_db(db, [{"Date": "2025-01-01", "Time": "08:00", "Pain Level": 5}])

        # CSV with the same entry plus one new one
        csv_content = "Date,Time,Pain Level\n2025-01-01,08:00,5\n2025-01-03,10:00,7\n"
        res = tc.post("/api/v1/data/import/csv",
                      files={"file": ("data.csv", io.BytesIO(csv_content.encode()), "text/csv")})
        assert res.status_code == 200
        body = res.json()
        assert body["imported_rows"] == 1, "Only the new row should be imported"
        assert body["skipped_rows"] == 1, "The duplicate row should be skipped"

    def test_csv_fully_duplicate_upload_is_a_noop(self, client):
        tc, db = client
        csv_content = "Date,Time,Pain Level\n2025-05-10,14:00,6\n"
        # First upload
        tc.post("/api/v1/data/import/csv",
                files={"file": ("data.csv", io.BytesIO(csv_content.encode()), "text/csv")})
        # Second upload of the same file
        res = tc.post("/api/v1/data/import/csv",
                      files={"file": ("data.csv", io.BytesIO(csv_content.encode()), "text/csv")})
        body = res.json()
        assert body["imported_rows"] == 0
        assert body["skipped_rows"] == 1

    def test_csv_rejects_invalid_pain_level(self, client):
        tc, db = client
        # Row 1: valid. Row 2: out of range. Row 3: non-numeric.
        csv_content = "Date,Time,Pain Level\n2025-06-01,08:00,4\n2025-06-02,08:00,15\n2025-06-03,08:00,bad\n"
        res = tc.post("/api/v1/data/import/csv",
                      files={"file": ("data.csv", io.BytesIO(csv_content.encode()), "text/csv")})
        assert res.status_code == 200
        body = res.json()
        assert body["imported_rows"] == 1, "Only the valid row should be imported"

    def test_csv_missing_time_column_returns_400(self, client):
        tc, _ = client
        csv_content = "Date,Pain Level\n2025-07-01,3\n"
        res = tc.post("/api/v1/data/import/csv",
                      files={"file": ("data.csv", io.BytesIO(csv_content.encode()), "text/csv")})
        assert res.status_code == 400
        assert "Time" in res.json()["detail"]


# ─── DB Import Tests ───────────────────────────────────────────────────────────

class TestDBImport:

    def test_db_import_uses_injected_db_path(self, client, tmp_path):
        """Verifies that import_db uses the dependency-injected db_path (Bug #2 regression)."""
        tc, target_db = client
        source_db = str(tmp_path / "source.db")
        make_test_db(source_db, [{"Date": "2025-02-01", "Time": "10:00", "Pain Level": 4}])

        with open(source_db, "rb") as f:
            res = tc.post("/api/v1/data/import/db",
                          files={"file": ("source.db", f, "application/octet-stream")})
        assert res.status_code == 200, f"Crashed: {res.text}"

    def test_db_import_merges_novel_rows(self, client, tmp_path):
        tc, target_db = client
        # Seed target with one row
        make_test_db(target_db, [{"Date": "2025-03-01", "Time": "08:00", "Pain Level": 2}])

        # Source has the same row plus a new one
        source_db = str(tmp_path / "source.db")
        make_test_db(source_db, [
            {"Date": "2025-03-01", "Time": "08:00", "Pain Level": 2},  # duplicate
            {"Date": "2025-03-02", "Time": "09:00", "Pain Level": 6},  # new
        ])

        with open(source_db, "rb") as f:
            res = tc.post("/api/v1/data/import/db",
                          files={"file": ("source.db", f, "application/octet-stream")})
        assert res.status_code == 200
        body = res.json()
        assert body["imported_rows"] == 1, "Only the novel row should be imported"
        assert body["skipped_rows"] == 1, "Duplicate should be skipped (Date+Time match)"

    def test_db_import_id_collision_does_not_duplicate(self, client, tmp_path):
        """
        Bug #3 regression: two DBs can have the same id for different entries.
        The old code would skip a valid row just because its id happens to exist
        in the target DB. The new code uses Date+Time, so this row should import.
        """
        tc, target_db = client
        # Target has id=1 -> 2025-04-01
        conn = sqlite3.connect(target_db)
        conn.execute('INSERT INTO migraine_log (id, Date, Time, "Pain Level") VALUES (1, "2025-04-01", "08:00", 3)')
        conn.commit(); conn.close()

        # Source has id=1 too, but for a DIFFERENT date
        source_db = str(tmp_path / "source.db")
        conn = sqlite3.connect(source_db)
        conn.execute("""
            CREATE TABLE migraine_log (
                id INTEGER PRIMARY KEY, Date TEXT, Time TEXT, "Pain Level" INTEGER,
                Medication TEXT, Dosage TEXT, Medications TEXT, Sleep TEXT,
                "Physical Activity" TEXT, Triggers TEXT, Notes TEXT,
                Location TEXT, Timezone TEXT, Latitude REAL, Longitude REAL
            )
        """)
        conn.execute('INSERT INTO migraine_log (id, Date, Time, "Pain Level") VALUES (1, "2025-04-02", "12:00", 7)')
        conn.commit(); conn.close()

        with open(source_db, "rb") as f:
            res = tc.post("/api/v1/data/import/db",
                          files={"file": ("source.db", f, "application/octet-stream")})
        assert res.status_code == 200
        body = res.json()
        assert body["imported_rows"] == 1, "Row with same id but different Date should be imported"
        assert body["skipped_rows"] == 0
