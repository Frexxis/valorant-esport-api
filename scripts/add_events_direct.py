"""
Add several events directly to the database to have some event data available
"""

import logging
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Event
from app import db

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def add_events():
    """
    Directly add some major Valorant events to the database
    """
    with app.app_context():
        # Check if we already have events
        event_count = Event.query.count()
        if event_count > 0:
            logger.info(f"Already have {event_count} events in database, skipping direct insert")
            return event_count
        
        events = [
            {
                'id': '1442', 
                'name': 'VCT 2025: Pacific Stage 1',
                'region': 'Pacific',
                'start_date': datetime(2025, 4, 5),
                'end_date': datetime(2025, 5, 25),
                'prize_pool': '$300,000',
                'status': 'ongoing',
                'event_url': 'https://www.vlr.gg/event/1442/vct-2025-pacific-stage-1',
                'logo_url': 'https://www.vlr.gg/img/vlr/event_images/1442.png'
            },
            {
                'id': '1443', 
                'name': 'VCT 2025: EMEA Stage 1',
                'region': 'EMEA',
                'start_date': datetime(2025, 4, 5),
                'end_date': datetime(2025, 5, 25),
                'prize_pool': '$300,000',
                'status': 'ongoing',
                'event_url': 'https://www.vlr.gg/event/1443/vct-2025-emea-stage-1',
                'logo_url': 'https://www.vlr.gg/img/vlr/event_images/1443.png'
            },
            {
                'id': '1444', 
                'name': 'VCT 2025: Americas Stage 1',
                'region': 'Americas',
                'start_date': datetime(2025, 4, 5),
                'end_date': datetime(2025, 5, 25),
                'prize_pool': '$300,000',
                'status': 'ongoing',
                'event_url': 'https://www.vlr.gg/event/1444/vct-2025-americas-stage-1',
                'logo_url': 'https://www.vlr.gg/img/vlr/event_images/1444.png'
            },
            {
                'id': '1520', 
                'name': 'VCT 2025: Masters Shanghai',
                'region': 'International',
                'start_date': datetime(2025, 6, 15),
                'end_date': datetime(2025, 6, 30),
                'prize_pool': '$1,000,000',
                'status': 'upcoming',
                'event_url': 'https://www.vlr.gg/event/1520/vct-2025-masters-shanghai',
                'logo_url': 'https://www.vlr.gg/img/vlr/event_images/1520.png'
            },
            {
                'id': '1601', 
                'name': 'VCT 2025: Champions Los Angeles',
                'region': 'International',
                'start_date': datetime(2025, 9, 1),
                'end_date': datetime(2025, 9, 20),
                'prize_pool': '$2,000,000',
                'status': 'upcoming',
                'event_url': 'https://www.vlr.gg/event/1601/vct-2025-champions-los-angeles',
                'logo_url': 'https://www.vlr.gg/img/vlr/event_images/1601.png'
            }
        ]
        
        try:
            for event_data in events:
                event = Event(**event_data)
                event.last_updated = datetime.utcnow()
                db.session.add(event)
                logger.info(f"Added event: {event_data['name']}")
            
            db.session.commit()
            logger.info(f"Successfully added {len(events)} events")
            return len(events)
        except Exception as e:
            db.session.rollback()
            logger.error(f"Error adding events: {str(e)}")
            return 0

if __name__ == "__main__":
    count = add_events()
    print(f"Added {count} events to the database")