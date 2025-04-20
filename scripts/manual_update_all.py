#!/usr/bin/env python3
"""
Manually run a full data update for matches, teams, and players.
This script can be used to refresh all data in the database.
"""

import os
import sys
import logging
import argparse
import time

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules
from app import app
from utils.db_operations import scrape_and_update_recent_matches, update_teams_and_players
from scrapers import vlr_scraper, bo3_scraper

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def run_full_update():
    """
    Run a full update of all data
    
    Returns:
        bool: True if successful, False otherwise
    """
    with app.app_context():
        try:
            logger.info("Starting full data update")
            
            # Step 1: Update matches
            logger.info("Updating matches")
            match_count = scrape_and_update_recent_matches(vlr_scraper, bo3_scraper, limit=50)
            logger.info(f"Updated {match_count} matches")
            
            # Add a delay to avoid overwhelming the server
            time.sleep(2)
            
            # Step 2: Update teams and players
            logger.info("Updating teams and players")
            team_count = update_teams_and_players()
            logger.info(f"Updated {team_count} teams")
            
            logger.info("Full data update completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Error in full data update: {str(e)}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Run a full data update for matches, teams, and players")
    
    logger.info("Starting full data update")
    result = run_full_update()
    
    if result:
        logger.info("Update completed successfully")
    else:
        logger.error("Update failed")