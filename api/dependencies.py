from fastapi import Header, Depends
from typing import Optional
from .utils import get_db_path

def get_db_path_dep(x_tester_mode: Optional[str] = Header(None)) -> str:
    """
    Dependency to get the correct database path.
    Checks for X-Tester-Mode header.
    """
    is_tester = x_tester_mode == 'true'
    return get_db_path(tester_mode=is_tester)
