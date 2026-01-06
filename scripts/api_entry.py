import sys
import os
import logging
import multiprocessing
import signal
from api.utils import get_data_dir

# 1. SETUP LOGGING
log_dir = get_data_dir()
os.makedirs(log_dir, exist_ok=True)
log_file = os.path.join(log_dir, "migraine_debug.log")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Configure Logging
    logging.basicConfig(
        filename=log_file,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filemode='w'
    )
    logger = logging.getLogger("api_entry")
    
    # Capture Uvicorn logs
    logging.getLogger("uvicorn").addHandler(logging.FileHandler(log_file))
    
    # --- SSL PATCH (PyInstaller) ---
    try:
        import certifi
        os.environ["REQUESTS_CA_BUNDLE"] = certifi.where()
        os.environ["SSL_CERT_FILE"] = certifi.where()
        logger.info(f"SSL Certs Configured: {certifi.where()}")
    except ImportError:
        logger.error("Certifi not found! SSL requests might fail.")
    # -------------------------------

    logger.info("Backend starting... (Lazy Loading Enabled)")
    logger.info(f"CWD: {os.getcwd()}")

    # --- SELF-CLEANING START ---
    # Attempt to kill any existing process named 'migraine-navigator-api' OR holding port 8000.
    # We use 'psutil' for robust, cross-platform process management.
    try:
        import psutil
        logger.info("Cleaning up old processes via psutil...")
        current_pid = os.getpid()
        
        for proc in psutil.process_iter(['pid', 'name']):
            try:
                if proc.info['pid'] == current_pid:
                    continue
                
                should_kill = False
                
                # Check 1: Name match
                if proc.info['name'] and 'migraine-navigator-api' in proc.info['name']:
                     should_kill = True
                
                # Check 2: Port 8000 match (more expensive, do only if name didn't match)
                if not should_kill:
                    try:
                        for conn in proc.connections():
                            if conn.laddr.port == 8000:
                                should_kill = True
                                break
                    except (psutil.AccessDenied, psutil.ZombieProcess):
                        pass

                if should_kill:
                    logger.warning(f"Found zombie process {proc.info['pid']} ({proc.info['name']}). Force killing...")
                    proc.kill()
                    
            except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
                pass
                
    except ImportError:
        logger.error("psutil not installed! Cannot perform robust cleanup.")
    except Exception as e:
        logger.error(f"Cleanup failed: {e}")
    # ---------------------------
    
    # 3. Import Main App
    try:
        import uvicorn
        from api.main import app
        import threading
        import time
        logger.info("FastAPI app imported.")

        # --- PROFESSIONAL LIFECYCLE MANAGEMENT (Stdin Monitor) ---
        # Robust Dead Man's Switch: Monitor stdin for EOF.
        # When the parent (Tauri) process dies, it closes the pipe to our stdin.
        def monitor_stdin():
            try:
                # Read 1 byte. blocks until input or EOF.
                # If EOF (parent dead), it returns empty bytes b''.
                if not sys.stdin.read(1):
                    logger.warning("Stdin closed (Parent died). Self-destructing...")
                    os._exit(0)
            except Exception as e:
                logger.error(f"Stdin monitor error: {e}")
                # If reading standard input fails, safer to assume we are detached
                os._exit(0)

        # Start monitoring in a background thread
        monitor_thread = threading.Thread(target=monitor_stdin, daemon=True)
        monitor_thread.start()
        # -------------------------------------------------------------

        config = uvicorn.Config(app, host="127.0.0.1", port=8000, log_config=None)
        server = uvicorn.Server(config)

        # Update handler to tell Uvicorn to stop
        def handle_exit(signum, frame):
            logger.info(f"Received signal {signum}. Stopping Uvicorn server...")
            server.should_exit = True
            
        signal.signal(signal.SIGTERM, handle_exit)
        signal.signal(signal.SIGINT, handle_exit)

        server.run()
        
    except Exception as e:
        logger.critical(f"CRITICAL FAILURE: {e}", exc_info=True)
        sys.exit(1)
