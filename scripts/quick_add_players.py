#!/usr/bin/env python3
"""
Quickly add players for specific top teams directly to the database
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

# Dictionary of top Valorant teams and their players from vlr.gg
PLAYERS_DATA = {
    "sentinels": [
        {"id": "1265", "name": "johnqt", "role": "IGL", "country": "Morocco"},
        {"id": "36245", "name": "N4RRATE", "role": "Entry", "country": "USA"},
        {"id": "3880", "name": "bang", "role": "Flex", "country": "USA"},
        {"id": "729", "name": "Zellsis", "role": "Entry", "country": "USA"},
        {"id": "4004", "name": "zekken", "role": "Flex", "country": "USA"},
        {"id": "8419", "name": "Reduxx", "role": "Sub", "country": "USA"}
    ],
    "loud": [
        {"id": "3386", "name": "aspas", "role": "Duelist", "country": "Brazil"},
        {"id": "2451", "name": "Less", "role": "Initiator", "country": "Brazil"},
        {"id": "16165", "name": "tuyz", "role": "Initiator", "country": "Brazil"},
        {"id": "3387", "name": "saadhak", "role": "Sentinel", "country": "Argentina"},
        {"id": "3388", "name": "cauanzin", "role": "Controller", "country": "Brazil"}
    ],
    "evil-geniuses": [
        {"id": "32677", "name": "C0M", "role": "Controller", "country": "USA"},
        {"id": "27725", "name": "Demon1", "role": "Duelist", "country": "USA"},
        {"id": "34496", "name": "Ethan", "role": "Initiator", "country": "USA"},
        {"id": "25744", "name": "Boostio", "role": "Flex", "country": "USA"},
        {"id": "11586", "name": "jawgemo", "role": "Flex", "country": "USA"}
    ],
    "drx": [
        {"id": "2761", "name": "stax", "role": "IGL", "country": "South Korea"},
        {"id": "2772", "name": "Rb", "role": "Duelist", "country": "South Korea"},
        {"id": "2764", "name": "Zest", "role": "Initiator", "country": "South Korea"},
        {"id": "2766", "name": "Foxy9", "role": "Sentinel", "country": "South Korea"},
        {"id": "21977", "name": "MaKo", "role": "Controller", "country": "South Korea"}
    ],
    "nrg-esports": [
        {"id": "2247", "name": "crashies", "role": "Initiator", "country": "USA"},
        {"id": "2250", "name": "Victor", "role": "Entry", "country": "USA"},
        {"id": "8735", "name": "ardiis", "role": "Flex", "country": "Latvia"},
        {"id": "4811", "name": "s0m", "role": "Flex", "country": "USA"},
        {"id": "16485", "name": "FiNESSE", "role": "Controller", "country": "USA"}
    ]
}

def add_all_players():
    """Add all defined players to the database"""
    with app.app_context():
        try:
            total_added = 0
            total_updated = 0
            
            for team_id, players in PLAYERS_DATA.items():
                # Check if team exists
                team = Team.query.filter_by(id=team_id).first()
                if not team:
                    logger.warning(f"Team {team_id} not found, skipping its players")
                    continue
                
                logger.info(f"Adding players for team: {team.name}")
                team_added = 0
                team_updated = 0
                
                for player_data in players:
                    try:
                        player_id = player_data["id"]
                        player = Player.query.filter_by(id=player_id).first()
                        
                        if player:
                            # Update existing player
                            player.name = player_data["name"]
                            player.team_id = team_id
                            player.role = player_data.get("role")
                            player.country = player_data.get("country")
                            player.last_updated = datetime.utcnow()
                            team_updated += 1
                            logger.info(f"Updated player: {player_data['name']}")
                        else:
                            # Create new player
                            player = Player(
                                id=player_id,
                                name=player_data["name"],
                                team_id=team_id,
                                role=player_data.get("role"),
                                country=player_data.get("country"),
                                last_updated=datetime.utcnow()
                            )
                            db.session.add(player)
                            team_added += 1
                            logger.info(f"Added new player: {player_data['name']}")
                        
                        # Commit after each player
                        db.session.commit()
                        
                    except Exception as e:
                        db.session.rollback()
                        logger.error(f"Error with player {player_data.get('name', 'unknown')}: {str(e)}")
                
                logger.info(f"Team {team.name}: Added {team_added}, Updated {team_updated} players")
                total_added += team_added
                total_updated += team_updated
            
            logger.info(f"ALL DONE! Total players added: {total_added}, updated: {total_updated}")
            return True
        
        except Exception as e:
            logger.error(f"Error adding players: {str(e)}")
            return False

if __name__ == "__main__":
    logger.info("Starting quick player addition for top teams")
    result = add_all_players()
    
    if result:
        logger.info("Successfully added players")
    else:
        logger.error("Failed to add players")