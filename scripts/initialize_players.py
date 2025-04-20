#!/usr/bin/env python3
"""
Initialize player data by scraping all teams currently in the database.
This script should be run after the database is populated with team data.
"""

import os
import sys
import logging
import argparse
import time

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the necessary modules
from app import app, db
from models import Team, Player
from scrapers import player_scraper
from utils.db_operations import upsert_player

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def initialize_player_data():
    """
    Scrape and add player data for all teams in the database
    """
    with app.app_context():
        try:
            # Get all teams from the database
            teams = Team.query.all()
            
            if not teams:
                logger.warning("No teams found in the database")
                return False
                
            logger.info(f"Found {len(teams)} teams in the database")
            
            # Initialize counters
            processed_teams = 0
            total_players_added = 0
            failed_teams = []
            
            # Process each team
            for team in teams:
                try:
                    logger.info(f"Processing team: {team.name} (ID: {team.id})")
                    
                    # Get players for the team
                    players = player_scraper.get_team_players(team.id)
                    
                    if not players:
                        logger.warning(f"No players found for team: {team.name}")
                        failed_teams.append(team.name)
                        continue
                        
                    logger.info(f"Found {len(players)} players for team: {team.name}")
                    
                    # Add each player
                    team_players_added = 0
                    for player_data in players:
                        try:
                            # Set the team ID
                            player_data['team_id'] = team.id
                            
                            # Add or update player
                            result = upsert_player(player_data)
                            
                            if result:
                                team_players_added += 1
                                logger.info(f"Added/updated player: {player_data['name']}")
                            else:
                                logger.warning(f"Failed to add/update player: {player_data['name']}")
                                
                        except Exception as e:
                            logger.error(f"Error processing player {player_data.get('name', 'unknown')}: {str(e)}")
                            continue
                    
                    # Add to total
                    total_players_added += team_players_added
                    processed_teams += 1
                    
                    # Update team's last_updated timestamp
                    team.last_updated = db.func.now()
                    db.session.commit()
                    
                    logger.info(f"Added {team_players_added} players for team: {team.name}")
                    
                    # Add a delay to avoid overwhelming the server
                    time.sleep(2)
                    
                except Exception as e:
                    logger.error(f"Error processing team {team.name}: {str(e)}")
                    failed_teams.append(team.name)
                    continue
            
            # Summary
            logger.info(f"Processed {processed_teams} teams")
            logger.info(f"Added/updated {total_players_added} players")
            
            if failed_teams:
                logger.warning(f"Failed to process {len(failed_teams)} teams: {', '.join(failed_teams)}")
                
            return True
            
        except Exception as e:
            logger.error(f"Error initializing player data: {str(e)}")
            return False

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Initialize player data for all teams")
    parser.add_argument("--limit", type=int, help="Limit the number of teams to process", default=None)
    
    args = parser.parse_args()
    
    logger.info("Starting player data initialization")
    result = initialize_player_data()
    
    if result:
        logger.info("Player data initialization completed")
    else:
        logger.error("Player data initialization failed")