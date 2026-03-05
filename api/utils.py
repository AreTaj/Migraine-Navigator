import sys
import os
import appdirs

def get_data_dir():
    """
    Returns the writable data directory.
    """
    if getattr(sys, 'frozen', False):
        # Production: Use User Data Directory
        app_data = appdirs.user_data_dir("MigraineNavigator", "AreTaj")
        os.makedirs(app_data, exist_ok=True)
        return app_data
    else:
        # Development: Use local project data folder
        return os.path.join(os.path.dirname(__file__), '..', 'data')

def get_db_path(db_name="migraine_log.db"):
    """
    Returns the path to the SQLite database.
    db_name: filename of the database to use (default: migraine_log.db).
    """
    # Sanitize: only allow basenames ending in .db, no path traversal
    basename = os.path.basename(db_name)
    if not basename.endswith('.db'):
        basename = 'migraine_log.db'
    return os.path.join(get_data_dir(), basename)

def list_databases():
    """
    Returns a list of all .db filenames in the data directory.
    Excludes empty databases (< 4KB, just a schema skeleton).
    """
    data_dir = get_data_dir()
    dbs = []
    if os.path.isdir(data_dir):
        for f in sorted(os.listdir(data_dir)):
            if f.endswith('.db'):
                full_path = os.path.join(data_dir, f)
                size = os.path.getsize(full_path)
                if size >= 4096:  # Skip empty skeleton DBs
                    dbs.append(f)
    return dbs
