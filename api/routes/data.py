from fastapi import APIRouter, File, UploadFile, HTTPException, Depends
from fastapi.responses import JSONResponse
# import pandas as pd # Moved to lazy load
# import io # Moved to lazy load
import sqlite3
import shutil
import os
from api.dependencies import get_db_path_dep
# train_and_evaluate from train_model is lazy-loaded in routes to avoid early matplotlib import

router = APIRouter(prefix="/data", tags=["data"])

REQUIRED_COLUMNS = ['Date', 'Time', 'Pain Level'] # Time required for deduplication

@router.post("/import/csv")
async def import_csv(file: UploadFile = File(...), db_path: str = Depends(get_db_path_dep)):
    """
    Import migraine log from a CSV file.
    Deduplicates on (Date, Time) before inserting.
    Triggers ML training if total records exceed threshold.
    """
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")

    try:
        import pandas as pd
        import io
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))

        # Validate required columns
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
            raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}")

        # Validate Pain Level values (must be numeric, 0-10)
        df['Pain Level'] = pd.to_numeric(df['Pain Level'], errors='coerce')
        invalid_pain = df['Pain Level'].isna() | (df['Pain Level'] < 0) | (df['Pain Level'] > 10)
        if invalid_pain.any():
            print(f"Dropping {invalid_pain.sum()} rows with invalid Pain Level values.")
            df = df[~invalid_pain]

        conn = sqlite3.connect(db_path)

        # Ensure table exists so we can safely read existing keys
        from services.entry_service import EntryService
        EntryService._create_table_if_not_exists(conn)

        # Load existing (Date, Time) pairs for deduplication
        existing = pd.read_sql("SELECT Date, Time FROM migraine_log", conn)
        existing_keys = set(zip(existing['Date'], existing['Time']))

        total_incoming = len(df)
        df = df[df.apply(lambda r: (str(r['Date']), str(r['Time'])) not in existing_keys, axis=1)]
        skipped_rows = total_incoming - len(df)

        if not df.empty:
            # Drop 'id' column if present to let SQLite auto-assign
            if 'id' in df.columns:
                df = df.drop(columns=['id'])
            df.to_sql('migraine_log', conn, if_exists='append', index=False)

        total_rows = pd.read_sql("SELECT COUNT(*) as c FROM migraine_log", conn)['c'][0]
        conn.close()

        return {
            "status": "success",
            "imported_rows": len(df),
            "skipped_rows": skipped_rows,
            "total_rows": int(total_rows),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"Import Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/db")
async def import_db(file: UploadFile = File(...), db_path: str = Depends(get_db_path_dep)):
    """
    Import from a legacy SQLite .db file.
    Deduplicates on (Date, Time), not id, since IDs differ across DB instances.
    """
    if not file.filename.endswith('.db') and not file.filename.endswith('.sqlite'):
        raise HTTPException(status_code=400, detail="File must be a SQLite DB.")

    temp_path = f"/tmp/{file.filename}"

    try:
        # Save upload to temp
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Fix Bug #2: use injected db_path, not the undefined get_db_path()
        conn = sqlite3.connect(db_path)

        # Ensure schema exists in main DB before attaching
        from services.entry_service import EntryService
        EntryService._create_table_if_not_exists(conn)

        conn.execute(f"ATTACH DATABASE '{temp_path}' AS source_db")

        # Count rows in source before merge to compute skipped
        source_count = conn.execute("SELECT COUNT(*) FROM source_db.migraine_log").fetchone()[0]
        pre_count = conn.execute("SELECT COUNT(*) FROM main.migraine_log").fetchone()[0]

        # Fix Bug #3: deduplicate by (Date, Time), not by id
        conn.execute("""
            INSERT INTO main.migraine_log
                (Date, Time, "Pain Level", Medication, Dosage, Medications,
                 Sleep, "Physical Activity", Triggers, Notes, Location, Timezone, Latitude, Longitude)
            SELECT
                s.Date, s.Time, s."Pain Level", s.Medication, s.Dosage, s.Medications,
                s.Sleep, s."Physical Activity", s.Triggers, s.Notes, s.Location, s.Timezone, s.Latitude, s.Longitude
            FROM source_db.migraine_log AS s
            WHERE NOT EXISTS (
                SELECT 1 FROM main.migraine_log AS m
                WHERE m.Date = s.Date AND m.Time = s.Time
            )
        """)
        conn.commit()

        import pandas as pd
        total_rows = conn.execute("SELECT COUNT(*) FROM main.migraine_log").fetchone()[0]
        imported_rows = total_rows - pre_count
        skipped_rows = source_count - imported_rows

        conn.execute("DETACH DATABASE source_db")
        conn.close()
        os.remove(temp_path)

        return {
            "status": "success",
            "imported_rows": imported_rows,
            "skipped_rows": skipped_rows,
            "total_rows": int(total_rows),
        }

    except HTTPException:
        raise
    except Exception as e:
        print(f"DB Import Error: {e}")
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))
