#!/usr/bin/env python3
"""
Add players directly to the database to ensure we have some player data
"""
import os
import sys
import logging
from datetime import datetime

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Player, Team

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Data for Sentinels team (directly from vlr.gg)
SENTINELS_PLAYERS = [
    {"id": "1265", "name": "johnqt", "role": "IGL", "country": "Morocco"},
    {"id": "36245", "name": "N4RRATE", "role": "Entry", "country": "USA"},
    {"id": "3880", "name": "bang", "role": "Flex", "country": "USA"},
    {"id": "729", "name": "Zellsis", "role": "Entry", "country": "USA"},
    {"id": "4004", "name": "zekken", "role": "Flex", "country": "USA"}
]

# Data for LOUD team (directly from vlr.gg)
LOUD_PLAYERS = [
    {"id": "3386", "name": "aspas", "role": "Duelist", "country": "Brazil"},
    {"id": "2451", "name": "Less", "role": "Initiator", "country": "Brazil"},
    {"id": "16165", "name": "tuyz", "role": "Initiator", "country": "Brazil"},
    {"id": "3387", "name": "saadhak", "role": "Sentinel", "country": "Argentina"},
    {"id": "3388", "name": "cauanzin", "role": "Controller", "country": "Brazil"}
]

def add_sentinels_players():
    """Add Sentinels players to the database"""
    with app.app_context():
        try:
            # Make sure the team exists
            team = Team.query.filter_by(id="sentinels").first()
            
            if not team:
                logger.error("Sentinels team not found in database")
                return False
                
            logger.info(f"Adding players for team: {team.name}")
            
            added = 0
            updated = 0
            
            # Add each player
            for player_data in SENTINELS_PLAYERS:
                try:
                    player_id = player_data["id"]
                    
                    # Check if player already exists
                    player = Player.query.filter_by(id=player_id).first()
                    
                    if player:
                        # Update existing player
                        logger.info(f"Updating player: {player_data['name']}")
                        player.name = player_data["name"]
                        player.team_id = team.id
                        player.role = player_data["role"]
                        player.country = player_data["country"]
                        player.last_updated = datetime.utcnow()
                        updated += 1
                    else:
                        # Create new player
                        logger.info(f"Adding new player: {player_data['name']}")
                        player = Player(
                            id=player_id,
                            name=player_data["name"],
                            team_id=team.id,
                            role=player_data["role"],
                            country=player_data["country"]
                        )
                        db.session.add(player)
                        added += 1
                    
                    # Save to database
                    db.session.commit()
                    
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error adding player {player_data['name']}: {str(e)}")
                
            logger.info(f"Added {added} new players and updated {updated} players for Sentinels")
            return True
            
        except Exception as e:
            logger.error(f"Error in add_sentinels_players: {str(e)}")
            return False

def add_loud_players():
    """Add LOUD players to the database"""
    with app.app_context():
        try:
            # Make sure the team exists
            team = Team.query.filter_by(id="loud").first()
            
            if not team:
                logger.error("LOUD team not found in database")
                return False
                
            logger.info(f"Adding players for team: {team.name}")
            
            added = 0
            updated = 0
            
            # Add each player
            for player_data in LOUD_PLAYERS:
                try:
                    player_id = player_data["id"]
                    
                    # Check if player already exists
                    player = Player.query.filter_by(id=player_id).first()
                    
                    if player:
                        # Update existing player
                        logger.info(f"Updating player: {player_data['name']}")
                        player.name = player_data["name"]
                        player.team_id = team.id
                        player.role = player_data["role"]
                        player.country = player_data["country"]
                        player.last_updated = datetime.utcnow()
                        updated += 1
                    else:
                        # Create new player
                        logger.info(f"Adding new player: {player_data['name']}")
                        player = Player(
                            id=player_id,
                            name=player_data["name"],
                            team_id=team.id,
                            role=player_data["role"],
                            country=player_data["country"]
                        )
                        db.session.add(player)
                        added += 1
                    
                    # Save to database
                    db.session.commit()
                    
                except Exception as e:
                    db.session.rollback()
                    logger.error(f"Error adding player {player_data['name']}: {str(e)}")
                
            logger.info(f"Added {added} new players and updated {updated} players for LOUD")
            return True
            
        except Exception as e:
            logger.error(f"Error in add_loud_players: {str(e)}")
            return False

if __name__ == "__main__":
    logger.info("Starting direct player addition...")
    
    # Add Sentinels players
    result_sentinels = add_sentinels_players()
    
    if result_sentinels:
        logger.info("Successfully added Sentinels players")
    else:
        logger.error("Failed to add Sentinels players")
    
    # Add LOUD players
    result_loud = add_loud_players()
    
    if result_loud:
        logger.info("Successfully added LOUD players")
    else:
        logger.error("Failed to add LOUD players")
    
    # Final status
    if result_sentinels and result_loud:
        logger.info("Successfully added all players")
    else:
        logger.error("Some player additions failed")