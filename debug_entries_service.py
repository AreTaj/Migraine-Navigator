import sys
import os
import traceback

# Add project root to path
sys.path.append(os.path.abspath(os.path.dirname(__file__)))

from services.entry_service import EntryService

DB_PATH = os.path.join(os.path.dirname(__file__), 'data', 'migraine_log.db')

print(f"Testing EntryService with DB at: {DB_PATH}")

try:
    df = EntryService.get_entries_from_db(DB_PATH)
    print("Success!")
    print(list(df.columns))
    print(df.head())
except Exception:
    traceback.print_exc()
