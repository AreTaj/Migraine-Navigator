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

REQUIRED_COLUMNS = ['Date', 'Pain Level'] # Minimal requirement

@router.post("/import/csv")
async def import_csv(file: UploadFile = File(...), db_path: str = Depends(get_db_path_dep)):
    """
    Import migraine log from a CSV file.
    Triggers ML training if total records exceed threshold.
    """
    # Check if file is CSV
    if not file.filename.endswith('.csv'):
        raise HTTPException(status_code=400, detail="Invalid file type. Please upload a CSV.")
    
    try:
        import pandas as pd
        import io
        content = await file.read()
        df = pd.read_csv(io.BytesIO(content))
        
        # Validation
        missing = [col for col in REQUIRED_COLUMNS if col not in df.columns]
        if missing:
             raise HTTPException(status_code=400, detail=f"Missing required columns: {missing}")
        
        # Insert into DB
        conn = sqlite3.connect(db_path)
        
        # Ensure target table exists (created by main app usually)
        # We rely on EntryService or similar, but for bulk insert pandas to_sql is faster if schema matches.
        # However, migraine_log has an 'id' primary key. We should append and ignore index.
        
        # Validate Columns
        required_cols = {'Date', 'Pain Level'} 
        missing = required_cols - set(df.columns)
        if missing:
             raise HTTPException(status_code=400, detail=f"CSV missing required columns: {missing}")
        
        df.to_sql('migraine_log', conn, if_exists='append', index=False)
        total_rows = pd.read_sql("SELECT COUNT(*) as c FROM migraine_log", conn)['c'][0]
        conn.close()
        
        # Trigger Training?
        training_triggered = False
        if total_rows > 60:
            try:
                print("Triggering ML Training due to data import...")
                from forecasting.train_model import train_and_evaluate
                train_and_evaluate()
                training_triggered = True
            except Exception as e:
                print(f"Training failed: {e}")
                # Don't fail the import just because training failed
        
        return {
            "status": "success", 
            "imported_rows": len(df), 
            "total_rows": int(total_rows),
            "training_triggered": training_triggered
        }
        
    except Exception as e:
        print(f"Import Error: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/import/db")
async def import_db(file: UploadFile = File(...), db_path: str = Depends(get_db_path_dep)):
    """
    Import from a legacy SQLite .db file.
    """
    if not file.filename.endswith('.db') and not file.filename.endswith('.sqlite'):
         raise HTTPException(status_code=400, detail="File must be a SQLite DB.")
         
    temp_path = f"/tmp/{file.filename}"
    
    try:
        # Save upload to temp
        with open(temp_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)
            
        # Merge Logic
        target_db = get_db_path()
        conn = sqlite3.connect(target_db)
        
        # Attach logic
        conn.execute(f"ATTACH DATABASE '{temp_path}' AS source_db")
        
        # Copy
        conn.execute("""
            INSERT INTO main.migraine_log 
            SELECT * FROM source_db.migraine_log 
            WHERE id NOT IN (SELECT id FROM main.migraine_log)
        """)
        
        conn.commit()
        import pandas as pd
        total_rows = pd.read_sql("SELECT COUNT(*) as c FROM migraine_log", conn)['c'][0]
        conn.detach("source_db") # Detach immediately
        conn.close()
        
        os.remove(temp_path)
        
         # Trigger Training?
        training_triggered = False
        if total_rows > 60:
            try:
                print("Triggering ML Training due to data import...")
                # Run synchronously for now
                from forecasting.train_model import train_and_evaluate
                train_and_evaluate()
                training_triggered = True
            except Exception as e:
                print(f"Training failed: {e}")
        
        return {
            "status": "success", 
            "total_rows": int(total_rows),
            "training_triggered": training_triggered
        }

    except Exception as e:
        print(f"DB Import Error: {e}")
        # Cleanup
        if os.path.exists(temp_path):
            os.remove(temp_path)
        raise HTTPException(status_code=500, detail=str(e))
