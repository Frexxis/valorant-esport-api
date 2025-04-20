import logging
import time
from datetime import datetime
from threading import Thread
from app import app
from scrapers import vlr_scraper, bo3_scraper
from utils.db_operations import scrape_and_update_recent_matches, update_teams_and_players

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Scheduling parameters
MATCH_UPDATE_INTERVAL = 300  # Update matches every 5 minutes (in seconds)
COMPREHENSIVE_MATCH_UPDATE_INTERVAL = 1800  # Update more matches every 30 minutes (in seconds)
TEAM_UPDATE_INTERVAL = 14400  # Update teams every 4 hours (in seconds)

def scheduler_thread():
    """
    Background thread for scheduled scraping
    """
    with app.app_context():
        logger.info("Starting scheduler thread")
        
        last_match_update = 0
        last_comprehensive_match_update = 0
        last_team_update = 0
        
        while True:
            current_time = time.time()
            
            # Quick update for live matches (every 5 minutes)
            if current_time - last_match_update >= MATCH_UPDATE_INTERVAL:
                logger.info("Running quick match update (focusing on live matches)")
                try:
                    # Only update a few recent matches for better responsiveness
                    scrape_and_update_recent_matches(vlr_scraper, bo3_scraper, limit=10)
                    last_match_update = current_time
                except Exception as e:
                    logger.error(f"Error in quick match update: {str(e)}")
            
            # More comprehensive match update (every 30 minutes)
            if current_time - last_comprehensive_match_update >= COMPREHENSIVE_MATCH_UPDATE_INTERVAL:
                logger.info("Running comprehensive match update")
                try:
                    # Update more matches in a comprehensive update
                    scrape_and_update_recent_matches(vlr_scraper, bo3_scraper, limit=50)
                    last_comprehensive_match_update = current_time
                except Exception as e:
                    logger.error(f"Error in comprehensive match update: {str(e)}")
            
            # Update teams and players (every 4 hours)
            if current_time - last_team_update >= TEAM_UPDATE_INTERVAL:
                logger.info("Running scheduled team update")
                try:
                    update_teams_and_players()
                    last_team_update = current_time
                except Exception as e:
                    logger.error(f"Error in scheduled team update: {str(e)}")
            
            # Sleep for 30 seconds before checking again (more responsive)
            time.sleep(30)


def start_scheduler():
    """
    Start the scheduler thread
    """
    try:
        # Initial data collection
        logger.info("Performing initial data collection")
        with app.app_context():
            scrape_and_update_recent_matches(vlr_scraper, bo3_scraper)
        
        # Start scheduler thread
        scheduler = Thread(target=scheduler_thread, daemon=True)
        scheduler.start()
        logger.info("Scheduler thread started")
    except Exception as e:
        logger.error(f"Error starting scheduler: {str(e)}")
