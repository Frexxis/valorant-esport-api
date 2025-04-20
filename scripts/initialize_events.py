"""
Initialize event data by scraping events from VLR.gg.
This script will fetch event data and populate the database.
"""

import logging
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from scrapers import vlr_scraper
from utils.db_operations import upsert_event

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_event_data():
    """
    Scrape and add event data to the database
    
    Returns:
        dict: Stats about the operation
    """
    with app.app_context():
        try:
            logger.info("Starting event data initialization")
            
            # Fetch events from VLR.gg
            events = vlr_scraper.get_events(limit=30)
            logger.info(f"Fetched {len(events)} events from VLR.gg")
            
            # Event counts
            events_added = 0
            events_updated = 0
            
            # Process each event
            for event_data in events:
                try:
                    event_id = event_data['id']
                    
                    # Get detailed event information
                    logger.info(f"Fetching details for event: {event_id}")
                    event_details = vlr_scraper.get_event_details(event_id)
                    
                    if event_details:
                        result = upsert_event(event_details)
                        if result:
                            if getattr(result, '_sa_instance_state').was_deleted:
                                events_updated += 1
                                logger.info(f"Updated event: {event_details.get('name')}")
                            else:
                                events_added += 1
                                logger.info(f"Added event: {event_details.get('name')}")
                        else:
                            logger.error(f"Failed to add/update event: {event_id}")
                    else:
                        # If detailed info not available, use the basic info
                        result = upsert_event(event_data)
                        if result:
                            if getattr(result, '_sa_instance_state').was_deleted:
                                events_updated += 1
                                logger.info(f"Updated event (basic info): {event_data.get('name')}")
                            else:
                                events_added += 1
                                logger.info(f"Added event (basic info): {event_data.get('name')}")
                        else:
                            logger.error(f"Failed to add/update event: {event_id}")
                except Exception as e:
                    logger.error(f"Error processing event {event_data.get('id', 'unknown')}: {str(e)}")
                    continue
            
            logger.info(f"Event initialization complete. Added: {events_added}, Updated: {events_updated}")
            
            return {
                "events_added": events_added,
                "events_updated": events_updated,
                "total_events": events_added + events_updated
            }
        
        except Exception as e:
            logger.error(f"Error initializing event data: {str(e)}")
            return {
                "events_added": 0,
                "events_updated": 0,
                "total_events": 0,
                "error": str(e)
            }

if __name__ == "__main__":
    stats = initialize_event_data()
    print(f"Event data initialization stats: {stats}")