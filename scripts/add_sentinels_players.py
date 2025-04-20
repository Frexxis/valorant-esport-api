#!/usr/bin/env python3
"""
Add Sentinels players directly to the database
"""
import os
import sys
import logging

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Player, Team

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# List of Sentinels players
SENTINELS_PLAYERS = [
    {
        "id": "1265",
        "name": "johnqt",
        "role": "IGL",
        "country": "Morocco"
    },
    {
        "id": "36245",
        "name": "N4RRATE",
        "role": "Entry",
        "country": "USA"
    },
    {
        "id": "3880",
        "name": "bang",
        "role": "Flex",
        "country": "USA"
    },
    {
        "id": "729",
        "name": "Zellsis",
        "role": "Entry",
        "country": "USA"
    },
    {
        "id": "4004",
        "name": "zekken",
        "role": "Flex",
        "country": "USA"
    },
    {
        "id": "8419",
        "name": "Reduxx",
        "role": "Sub",
        "country": "USA"
    },
    {
        "id": "45",
        "name": "SicK",
        "role": "Inactive",
        "country": "USA"
    }
]

def add_sentinels_players():
    """
    Add or update Sentinels players in the database
    """
    with app.app_context():
        try:
            # Ensure Sentinels team exists
            team = Team.query.filter_by(id="sentinels").first()
            if not team:
                logger.error("Sentinels team not found in database. Creating it now.")
                team = Team(
                    id="sentinels",
                    name="Sentinels",
                    region="North America"
                )
                db.session.add(team)
                db.session.commit()
            
            added_count = 0
            updated_count = 0
            
            # Add each player
            for player_data in SENTINELS_PLAYERS:
                try:
                    player_id = player_data["id"]
                    player = Player.query.filter_by(id=player_id).first()
                    
                    if player:
                        # Update existing player
                        player.name = player_data["name"]
                        player.team_id = "sentinels"
                        player.role = player_data["role"]
                        player.country = player_data["country"]
                        player.last_updated = db.func.now()
                        updated_count += 1
                        logger.info(f"Updated player: {player_data['name']}")
                    else:
                        # Create new player
                        player = Player(
                            id=player_id,
                            name=player_data["name"],
                            team_id="sentinels",
                            role=player_data["role"],
                            country=player_data["country"]
                        )
                        db.session.add(player)
                        added_count += 1
                        logger.info(f"Added new player: {player_data['name']}")
                    
                    # Commit after each player
                    db.session.commit()
                    
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error adding player {player_data['name']}: {str(e)}")
            
            logger.info(f"Completed adding Sentinels players. Added: {added_count}, Updated: {updated_count}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding Sentinels players: {str(e)}")
            return False

if __name__ == "__main__":
    logger.info("Starting Sentinels player addition")
    result = add_sentinels_players()
    
    if result:
        logger.info("Successfully added Sentinels players")
    else:
        logger.error("Failed to add Sentinels players")