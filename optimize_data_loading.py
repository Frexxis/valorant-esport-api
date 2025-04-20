"""
Optimize data loading by modifying the scheduler to load data in the background
"""
import sys
import os
import threading
from datetime import datetime
import time

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from utils.scheduling import start_scheduler

def apply_optimization():
    """
    Modify the scheduling to run in true background threads
    """
    with app.app_context():
        # Start the scheduler in a separate thread
        scheduler_thread = threading.Thread(target=start_scheduler)
        scheduler_thread.daemon = True  # Make thread a daemon so it exits when main thread exits
        scheduler_thread.start()
        
        print("Started scheduler in background thread.")
        print("This allows API endpoints to be accessible immediately.")

if __name__ == "__main__":
    apply_optimization()