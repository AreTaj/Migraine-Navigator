import sys
import os
import appdirs

def get_data_dir():
    """
    Returns the writable data directory.
    """
    if getattr(sys, 'frozen', False):
        # Production: Use User Data Directory
        # e.g., /Users/User/Library/Application Support/AreTaj/MigraineNavigator
        app_data = appdirs.user_data_dir("MigraineNavigator", "AreTaj")
        os.makedirs(app_data, exist_ok=True)
        return app_data
    else:
        # Development: Use local project data folder
        # api/utils.py -> .. -> .. -> data
        return os.path.join(os.path.dirname(__file__), '..', 'data')

def get_db_path():
    """
    Returns the path to the SQLite database.
    """
    return os.path.join(get_data_dir(), 'migraine_log.db')
