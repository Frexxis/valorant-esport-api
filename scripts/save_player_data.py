#!/usr/bin/env python3
"""
Save player data for specific teams directly
"""

import os
import sys
import logging
import json
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

def save_team_players(team_id):
    """
    Save players for a specific team
    
    Args:
        team_id (str): ID of the team
        
    Returns:
        bool: Success status
    """
    with app.app_context():
        try:
            # Check if team exists
            team = Team.query.filter_by(id=team_id).first()
            
            if not team:
                logger.error(f"Team not found: {team_id}")
                return False
                
            logger.info(f"Processing team: {team.name} (ID: {team.id})")
            
            # Scrape player data
            players = player_scraper.get_team_players(team_id)
            
            if not players:
                logger.warning(f"No players found for team: {team.name}")
                return False
                
            logger.info(f"Found {len(players)} players for team: {team.name}")
            
            # Save each player
            players_added = 0
            for player_data in players:
                try:
                    # Set the team ID
                    player_data['team_id'] = team.id
                    
                    # Add or update player
                    result = upsert_player(player_data)
                    
                    if result:
                        players_added += 1
                        logger.info(f"Added/updated player: {player_data['name']} (ID: {player_data['id']})")
                    else:
                        logger.warning(f"Failed to add/update player: {player_data['name']}")
                        
                except Exception as e:
                    logger.error(f"Error processing player {player_data.get('name', 'unknown')}: {str(e)}")
                    continue
            
            # Update team's last_updated timestamp
            team.last_updated = db.func.now()
            db.session.commit()
            
            logger.info(f"Successfully added/updated {players_added} players for team: {team.name}")
            return True
            
        except Exception as e:
            logger.error(f"Error saving players for team {team_id}: {str(e)}")
            return False

def get_team_list(limit=5):
    """
    Get a list of team IDs to process
    
    Args:
        limit (int): Maximum number of teams to return
        
    Returns:
        list: List of team IDs
    """
    with app.app_context():
        try:
            # Get popular teams first
            popular_teams = ['sentinels', 'loud', 'nrg-esports', 'drx', 'evil-geniuses', '100-thieves']
            
            # Get additional teams from database
            db_teams = Team.query.filter(~Team.id.in_(popular_teams)).limit(limit - len(popular_teams)).all()
            
            # Combine lists
            all_teams = popular_teams + [t.id for t in db_teams]
            
            # Return the limited list
            return all_teams[:limit]
            
        except Exception as e:
            logger.error(f"Error getting team list: {str(e)}")
            return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Save player data for specific teams")
    parser.add_argument("--team", help="Team ID to save players for (omit to process multiple teams)")
    parser.add_argument("--limit", type=int, help="Limit the number of teams to process", default=5)
    parser.add_argument("--sleep", type=int, help="Sleep time between teams in seconds", default=3)
    
    args = parser.parse_args()
    
    if args.team:
        # Process a single team
        logger.info(f"Saving players for team: {args.team}")
        result = save_team_players(args.team)
        
        if result:
            logger.info(f"Successfully saved players for team: {args.team}")
        else:
            logger.error(f"Failed to save players for team: {args.team}")
    else:
        # Process multiple teams
        logger.info(f"Saving players for up to {args.limit} teams")
        
        # Get team list
        teams = get_team_list(args.limit)
        
        if not teams:
            logger.error("No teams found to process")
            sys.exit(1)
            
        logger.info(f"Found {len(teams)} teams to process")
        
        # Process each team
        successful = 0
        for i, team_id in enumerate(teams):
            logger.info(f"Processing team {i+1}/{len(teams)}: {team_id}")
            
            result = save_team_players(team_id)
            
            if result:
                successful += 1
            
            # Sleep between teams to avoid rate limiting
            if i < len(teams) - 1:
                logger.info(f"Sleeping for {args.sleep} seconds before next team...")
                time.sleep(args.sleep)
        
        logger.info(f"Completed processing {len(teams)} teams")
        logger.info(f"Successfully saved players for {successful}/{len(teams)} teams")