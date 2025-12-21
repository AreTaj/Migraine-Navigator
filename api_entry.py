import sys
import os
import logging
import multiprocessing
import signal

# 1. SETUP LOGGING
desktop_log = os.path.expanduser("~/Desktop/migraine_debug.log")

if __name__ == "__main__":
    multiprocessing.freeze_support()
    
    # Configure Logging
    logging.basicConfig(
        filename=desktop_log,
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        filemode='w'
    )
    logger = logging.getLogger("api_entry")
    
    # Capture Uvicorn logs
    logging.getLogger("uvicorn").addHandler(logging.FileHandler(desktop_log))
    
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
    
    # Custom Signal Handling (Safe Shutdown)
    def handle_exit(signum, frame):
        logger.info(f"Received signal {signum}. Initiating safe shutdown...")
        # Since we disable Uvicorn's handlers, we must manually exit.
        # sys.exit(0) triggers standard Python shutdown (finally blocks, atexit).
        sys.exit(0)
    
    signal.signal(signal.SIGTERM, handle_exit)
    signal.signal(signal.SIGINT, handle_exit)

    # 3. Import Main App
    try:
        import uvicorn
        from api.main import app
        logger.info("FastAPI app imported.")
        
        # Run Uvicorn without default handlers (Tauri/Safe Exit handles this)
        # Note: older Uvicorn versions don't support install_signal_handlers, 
        # so we rely on our signal handlers overriding defaults or just let them race.
        # But 'server.run' is better if we need fine control. For now, revert simple run.
        uvicorn.run(app, host="127.0.0.1", port=8000, log_config=None)
        
    except Exception as e:
        logger.critical(f"CRITICAL FAILURE: {e}", exc_info=True)
        sys.exit(1)
