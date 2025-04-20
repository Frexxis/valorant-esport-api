#!/usr/bin/env python3
"""
Update player data for a specific team.
This script can be run to update a single team's player roster.
"""

import os
import sys
import logging
import argparse

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules
import json
from datetime import datetime
from app import app, db
from models import Team, Player
from scrapers import player_scraper
from utils.db_operations import upsert_player

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def update_team_players(team_id):
    """
    Update player data for a specific team
    
    Args:
        team_id (str): ID of the team to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    with app.app_context():
        try:
            logger.info(f"Updating team: {team_id}")
            
            # Get the team
            team = Team.query.filter_by(id=team_id).first()
            
            if not team:
                logger.warning(f"Team not found: {team_id}")
                return False
                
            # Get players for this team
            players = player_scraper.get_team_players(team_id)
            
            if not players:
                logger.warning(f"No players found for team: {team.name}")
                return False
                
            logger.info(f"Found {len(players)} players for team: {team.name}")
            
            # Add each player
            player_count = 0
            for player_data in players:
                try:
                    # Try to get more detailed player data
                    player_detail = player_scraper.get_player_details(player_data['id'])
                    
                    if player_detail:
                        # Use detailed data
                        data_to_save = player_detail
                    else:
                        # Use basic data
                        data_to_save = player_data
                        data_to_save['team_id'] = team.id
                    
                    # Add or update player
                    result = upsert_player(data_to_save)
                    
                    if result:
                        player_count += 1
                        logger.info(f"Added/updated player: {player_data['name']}")
                    else:
                        logger.warning(f"Failed to add/update player: {player_data['name']}")
                        
                except Exception as e:
                    logger.error(f"Error processing player {player_data.get('name', 'unknown')}: {str(e)}")
                    continue
            
            # Update team's "last_updated" timestamp
            team.last_updated = datetime.utcnow()
            db.session.commit()
            
            logger.info(f"Successfully updated team: {team.name} with {player_count} players")
            return True
            
        except Exception as e:
            logger.error(f"Error updating team: {str(e)}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Update player data for a specific team")
    parser.add_argument("team_id", help="ID of the team to update")
    
    args = parser.parse_args()
    
    logger.info(f"Starting update for team: {args.team_id}")
    result = update_team_players(args.team_id)
    
    if result:
        logger.info("Team update completed successfully")
    else:
        logger.error("Team update failed")