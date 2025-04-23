# datasync/tasks.py
import threading
import time
import logging
from .sync import fetch_and_update_data

logger = logging.getLogger(__name__)

def periodic_task(interval):
    """
    Periodically runs the fetch_and_update_data function.
    """
    logger.info("Periodic task has started.")
    while True:
        try:
            fetch_and_update_data()
            logger.info('Data synced successfully.')
        except Exception as e:
            logger.error(f"Error during fetch_and_update_data: {e}")
        time.sleep(interval)

def start_background_task():
    logger.info("Starting background task.")
    task_thread = threading.Thread(target=periodic_task, args=(4,))  # Interval set to 4 seconds
    task_thread.daemon = True
    task_thread.start()