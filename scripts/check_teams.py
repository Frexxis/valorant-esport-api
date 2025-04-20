#!/usr/bin/env python3
"""
Check teams in the database and print information about them.
"""

import os
import sys
import logging

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules
from app import app, db
from models import Team, Player

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def show_teams():
    """
    Show information about teams in the database
    """
    with app.app_context():
        # Count teams
        team_count = Team.query.count()
        print(f"Teams in database: {team_count}")
        
        # Get first 5 teams
        teams = Team.query.limit(5).all()
        
        print("\nFirst 5 teams:")
        for team in teams:
            print(f"Team ID: {team.id}, Name: {team.name}, Region: {team.region}")
            
def show_players():
    """
    Show information about players in the database
    """
    with app.app_context():
        # Count players
        player_count = Player.query.count()
        print(f"\nPlayers in database: {player_count}")
        
        # Get first 5 players
        players = Player.query.limit(5).all()
        
        print("\nFirst 5 players:")
        for player in players:
            print(f"Player ID: {player.id}, Name: {player.name}, Team: {player.team_id}")
            
if __name__ == "__main__":
    show_teams()
    show_players()