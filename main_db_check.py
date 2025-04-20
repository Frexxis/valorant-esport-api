"""
A script to check if events are properly stored in the database
"""
import sys
import os
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app
from models import Event

with app.app_context():
    # Check if events exist in the database
    events = Event.query.all()
    print(f"Found {len(events)} events in database:")
    for event in events:
        print(f"- {event.id}: {event.name} ({event.region}) - {event.status}")