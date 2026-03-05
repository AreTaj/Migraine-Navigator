from fastapi import Header
from typing import Optional
from .utils import get_db_path

def get_db_path_dep(x_active_db: Optional[str] = Header(None)) -> str:
    """
    Dependency to get the correct database path.
    Checks for X-Active-DB header to determine which database file to use.
    """
    db_name = x_active_db if x_active_db else "migraine_log.db"
    return get_db_path(db_name=db_name)
