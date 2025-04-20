#!/usr/bin/env python3
"""
Directly save player data for specific teams, bypassing initial data collection
"""
import os
import sys
import logging
import time

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from app import app, db
from models import Team, Player
from scrapers import player_scraper
from sqlalchemy.exc import SQLAlchemyError

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def save_players(team_id):
    """
    Directly save players for a team to the database
    """
    with app.app_context():
        try:
            # Get the team
            team = Team.query.filter_by(id=team_id).first()
            if not team:
                logger.error(f"Team not found with ID: {team_id}")
                return False
                
            logger.info(f"Processing team: {team.name} (ID: {team.id})")
            
            # Get player data
            logger.info(f"Fetching players for team: {team_id}")
            players = player_scraper.get_team_players(team_id)
            
            if not players:
                logger.warning(f"No players found for team: {team_id}")
                return False
                
            logger.info(f"Found {len(players)} players")
            
            # Save each player
            for player_data in players:
                try:
                    player_id = player_data['id']
                    player_name = player_data['name']
                    
                    # Check if player exists
                    player = Player.query.filter_by(id=player_id).first()
                    
                    if player:
                        # Update existing player
                        logger.info(f"Updating player: {player_name}")
                        player.name = player_name
                        player.team_id = team_id
                        player.role = player_data.get('role')
                        player.country = player_data.get('country')
                        player.last_updated = db.func.now()
                    else:
                        # Create new player
                        logger.info(f"Creating new player: {player_name}")
                        player = Player(
                            id=player_id,
                            name=player_name,
                            team_id=team_id,
                            role=player_data.get('role'),
                            country=player_data.get('country')
                        )
                        db.session.add(player)
                    
                    # Commit the changes
                    db.session.commit()
                    logger.info(f"Successfully saved player: {player_name}")
                    
                except SQLAlchemyError as e:
                    db.session.rollback()
                    logger.error(f"Database error saving player {player_data.get('name')}: {str(e)}")
                except Exception as e:
                    logger.error(f"Error saving player {player_data.get('name')}: {str(e)}")
            
            logger.info(f"Completed processing players for team: {team.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error in save_players: {str(e)}")
            return False

if __name__ == "__main__":
    # Process some popular teams
    teams = [
        'sentinels',
        'loud',
        'evil-geniuses',
        'drx',
        'nrg-esports'
    ]
    
    successful = 0
    failed = []
    
    for i, team_id in enumerate(teams):
        logger.info(f"Processing team {i+1}/{len(teams)}: {team_id}")
        
        result = save_players(team_id)
        
        if result:
            successful += 1
            logger.info(f"Successfully processed team: {team_id}")
        else:
            failed.append(team_id)
            logger.error(f"Failed to process team: {team_id}")
        
        # Sleep to avoid rate limiting
        if i < len(teams) - 1:
            sleep_time = 3
            logger.info(f"Sleeping for {sleep_time} seconds...")
            time.sleep(sleep_time)
    
    logger.info("Player saving process complete")
    logger.info(f"Successfully processed {successful}/{len(teams)} teams")
    
    if failed:
        logger.warning(f"Failed teams: {', '.join(failed)}")