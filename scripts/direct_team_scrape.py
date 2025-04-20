#!/usr/bin/env python3
"""
Script to directly test player scraping for a specific team.
This is a simpler script without using the database operations.
"""

import os
import sys
import logging
import argparse
import time
import json

# Add parent directory to path to allow importing app modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

# Import the scraper
from scrapers import player_scraper

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def scrape_team_players(team_id):
    """
    Get players for a team without saving to database
    
    Args:
        team_id (str): ID of the team to scrape
        
    Returns:
        list: List of player dictionaries
    """
    try:
        logger.info(f"Scraping team: {team_id}")
        
        # Get players for this team
        players = player_scraper.get_team_players(team_id)
        
        if not players:
            logger.warning(f"No players found for team: {team_id}")
            return []
            
        logger.info(f"Found {len(players)} players")
        
        for player in players:
            logger.info(f"Player: {player.get('name', 'Unknown')} ({player.get('id', 'Unknown')})")
            
            # Add a delay to avoid rate limiting
            time.sleep(1)
            
            # Try to get player details
            try:
                player_detail = player_scraper.get_player_details(player['id'])
                if player_detail:
                    logger.info(f"Got details for player: {player_detail.get('name', 'Unknown')}")
                    logger.info(f"Role: {player_detail.get('role', 'Unknown')}")
                    logger.info(f"Country: {player_detail.get('country', 'Unknown')}")
                    if 'stats' in player_detail and player_detail['stats']:
                        logger.info(f"Stats available: {list(player_detail['stats'].keys())}")
                else:
                    logger.warning(f"Could not get details for player: {player.get('name', 'Unknown')}")
            except Exception as e:
                logger.error(f"Error getting player details: {str(e)}")
                continue
            
            logger.info("-" * 30)
            
        return players
        
    except Exception as e:
        logger.error(f"Error scraping team: {str(e)}")
        return []

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Scrape player data for a specific team")
    parser.add_argument("team_id", help="ID of the team to scrape")
    parser.add_argument("--output", help="Output file path for JSON data", default=None)
    
    args = parser.parse_args()
    
    logger.info(f"Starting direct scrape for team: {args.team_id}")
    players = scrape_team_players(args.team_id)
    
    if args.output:
        with open(args.output, 'w') as f:
            json.dump(players, f, indent=2)
            logger.info(f"Saved {len(players)} players to {args.output}")
            
    logger.info(f"Found {len(players)} players for team: {args.team_id}")