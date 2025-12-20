import uvicorn
import multiprocessing
from api.main import app

if __name__ == "__main__":
    multiprocessing.freeze_support()  # Required for PyInstaller
    uvicorn.run(app, host="127.0.0.1", port=8000)
