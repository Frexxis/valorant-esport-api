"""
A simple script to show events directly from the database
"""
import sys
import json
from app import app
from models import Event

def show_events():
    """
    Display all events in the database
    """
    with app.app_context():
        events = Event.query.all()
        print(f"Found {len(events)} events:")
        
        for event in events:
            event_dict = {
                "id": event.id,
                "name": event.name,
                "region": event.region,
                "status": event.status,
                "start_date": str(event.start_date) if event.start_date else None,
                "end_date": str(event.end_date) if event.end_date else None,
                "prize_pool": event.prize_pool,
                "event_url": event.event_url,
                "logo_url": event.logo_url
            }
            print(json.dumps(event_dict, indent=2))
            print("---")

if __name__ == "__main__":
    show_events()