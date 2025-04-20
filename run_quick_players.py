#!/usr/bin/env python3
"""
Run the quick player addition script directly
"""
from app import app, db
from models import Team, Player
from datetime import datetime

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

def add_players():
    with app.app_context():
        print("Starting player addition")
        
        for team_id, players in PLAYERS_DATA.items():
            team = Team.query.filter_by(id=team_id).first()
            if not team:
                print(f"Team {team_id} not found, skipping")
                continue
                
            print(f"Adding players for {team.name}")
            
            for player_data in players:
                try:
                    player_id = player_data["id"]
                    existing = Player.query.filter_by(id=player_id).first()
                    
                    if existing:
                        existing.name = player_data["name"]
                        existing.team_id = team_id
                        existing.role = player_data.get("role")
                        existing.country = player_data.get("country")
                        existing.last_updated = datetime.utcnow()
                        print(f"Updated {player_data['name']}")
                    else:
                        player = Player(
                            id=player_id,
                            name=player_data["name"],
                            team_id=team_id,
                            role=player_data.get("role"),
                            country=player_data.get("country"),
                            last_updated=datetime.utcnow()
                        )
                        db.session.add(player)
                        print(f"Added {player_data['name']}")
                    
                    db.session.commit()
                    
                except Exception as e:
                    db.session.rollback()
                    print(f"Error with {player_data.get('name')}: {str(e)}")
        
        print("Player addition complete")

if __name__ == "__main__":
    add_players()