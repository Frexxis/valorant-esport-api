#!/usr/bin/env python3
"""
Process all teams in the database to extract and save their players.
This script will fetch and update player data for all teams.
"""

import os
import sys
import logging
import time
import argparse

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

def process_all_teams(limit=None, sleep_time=5):
    """
    Process all teams and save their players
    
    Args:
        limit (int, optional): Maximum number of teams to process
        sleep_time (int, optional): Sleep time between team scraping to avoid rate limiting
        
    Returns:
        dict: Stats about the operation
    """
    with app.app_context():
        try:
            # Get all teams from the database
            teams_query = Team.query
            
            # Apply limit if provided
            if limit and isinstance(limit, int) and limit > 0:
                teams_query = teams_query.limit(limit)
                
            teams = teams_query.all()
            
            if not teams:
                logger.warning("No teams found in the database")
                return {"success": False, "error": "No teams found"}
                
            logger.info(f"Found {len(teams)} teams in the database")
            
            # Initialize counters
            stats = {
                "total_teams": len(teams),
                "processed_teams": 0,
                "total_players_added": 0,
                "failed_teams": [],
                "successful_teams": []
            }
            
            # Process each team
            for team in teams:
                try:
                    logger.info(f"Processing team: {team.name} (ID: {team.id})")
                    
                    # Get players for the team
                    players = player_scraper.get_team_players(team.id)
                    
                    if not players:
                        logger.warning(f"No players found for team: {team.name}")
                        stats["failed_teams"].append(team.name)
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
                    stats["total_players_added"] += team_players_added
                    stats["processed_teams"] += 1
                    stats["successful_teams"].append(team.name)
                    
                    # Update team's last_updated timestamp
                    team.last_updated = db.func.now()
                    db.session.commit()
                    
                    logger.info(f"Added {team_players_added} players for team: {team.name}")
                    
                    # Add a delay to avoid overwhelming the server
                    logger.info(f"Sleeping for {sleep_time} seconds before next team...")
                    time.sleep(sleep_time)
                    
                except Exception as e:
                    logger.error(f"Error processing team {team.name}: {str(e)}")
                    stats["failed_teams"].append(team.name)
                    continue
            
            # Summary
            logger.info(f"Processed {stats['processed_teams']} teams")
            logger.info(f"Added/updated {stats['total_players_added']} players")
            
            if stats["failed_teams"]:
                logger.warning(f"Failed to process {len(stats['failed_teams'])} teams: {', '.join(stats['failed_teams'])}")
                
            stats["success"] = True
            return stats
            
        except Exception as e:
            logger.error(f"Error processing teams: {str(e)}")
            return {"success": False, "error": str(e)}

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Process all teams and save their players")
    parser.add_argument("--limit", type=int, help="Limit the number of teams to process", default=None)
    parser.add_argument("--sleep", type=int, help="Sleep time between teams in seconds", default=5)
    
    args = parser.parse_args()
    
    logger.info("Starting team player extraction process")
    stats = process_all_teams(limit=args.limit, sleep_time=args.sleep)
    
    if stats["success"]:
        logger.info("Team processing completed successfully")
        logger.info(f"Processed {stats['processed_teams']} of {stats['total_teams']} teams")
        logger.info(f"Added {stats['total_players_added']} players")
        
        if stats["failed_teams"]:
            logger.warning(f"Failed teams: {', '.join(stats['failed_teams'])}")
    else:
        logger.error(f"Team processing failed: {stats.get('error', 'Unknown error')}")