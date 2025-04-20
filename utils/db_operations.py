import logging
import json
from datetime import datetime
from app import db
from models import Player, Team, Match, MapStatistic, Event

# Setup logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def upsert_team(team_data):
    """
    Insert or update a team in the database
    
    Args:
        team_data (dict): Team data
        
    Returns:
        Team: The inserted or updated team object
    """
    try:
        team = Team.query.filter_by(id=team_data['id']).first()
        
        if not team:
            # Create new team
            team = Team(
                id=team_data['id'],
                name=team_data['name'],
                region=team_data.get('region'),
                logo_url=team_data.get('logo_url')
            )
            logger.info(f"Creating new team: {team_data['name']}")
        else:
            # Update existing team
            team.name = team_data['name']
            team.region = team_data.get('region')
            team.logo_url = team_data.get('logo_url')
            logger.info(f"Updating existing team: {team_data['name']}")
        
        # Handle stats
        if 'stats' in team_data and team_data['stats']:
            team.stats = json.dumps(team_data['stats'])
        
        team.last_updated = datetime.utcnow()
        
        # Add to session and commit
        db.session.add(team)
        db.session.commit()
        
        # Process players if available
        if 'players' in team_data and team_data['players']:
            for player_data in team_data['players']:
                player_data['team_id'] = team.id
                upsert_player(player_data)
        
        return team
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in upsert_team: {str(e)}")
        return None


def upsert_player(player_data):
    """
    Insert or update a player in the database
    
    Args:
        player_data (dict): Player data
        
    Returns:
        Player: The inserted or updated player object
    """
    try:
        player = Player.query.filter_by(id=player_data['id']).first()
        
        if not player:
            # Create new player
            player = Player(
                id=player_data['id'],
                name=player_data['name'],
                team_id=player_data.get('team_id'),
                role=player_data.get('role'),
                country=player_data.get('country')
            )
            logger.info(f"Creating new player: {player_data['name']}")
        else:
            # Update existing player
            player.name = player_data['name']
            player.team_id = player_data.get('team_id')
            player.role = player_data.get('role')
            player.country = player_data.get('country')
            logger.info(f"Updating existing player: {player_data['name']}")
        
        # Handle stats
        if 'stats' in player_data and player_data['stats']:
            player.stats = json.dumps(player_data['stats'])
        
        player.last_updated = datetime.utcnow()
        
        # Add to session and commit
        db.session.add(player)
        db.session.commit()
        
        return player
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in upsert_player: {str(e)}")
        return None


def upsert_match(match_data):
    """
    Insert or update a match in the database
    
    Args:
        match_data (dict): Match data
        
    Returns:
        Match: The inserted or updated match object
    """
    try:
        match = Match.query.filter_by(id=match_data['id']).first()
        
        # First ensure teams exist in the database
        if 'team1_id' in match_data and 'team1_name' in match_data:
            team1_data = {
                'id': match_data['team1_id'],
                'name': match_data['team1_name']
            }
            upsert_team(team1_data)
        
        if 'team2_id' in match_data and 'team2_name' in match_data:
            team2_data = {
                'id': match_data['team2_id'],
                'name': match_data['team2_name']
            }
            upsert_team(team2_data)
        
        if not match:
            # Create new match
            match = Match(
                id=match_data['id'],
                team1_id=match_data.get('team1_id'),
                team2_id=match_data.get('team2_id'),
                date=match_data.get('date'),
                event_name=match_data.get('event_name'),
                status=match_data.get('status'),
                score=match_data.get('score'),
                match_url=match_data.get('match_url')
            )
            logger.info(f"Creating new match: {match_data['id']}")
        else:
            # Update existing match
            match.team1_id = match_data.get('team1_id')
            match.team2_id = match_data.get('team2_id')
            match.date = match_data.get('date')
            match.event_name = match_data.get('event_name')
            match.status = match_data.get('status')
            match.score = match_data.get('score')
            match.match_url = match_data.get('match_url')
            logger.info(f"Updating existing match: {match_data['id']}")
        
        match.last_updated = datetime.utcnow()
        
        # Add to session and commit
        db.session.add(match)
        db.session.commit()
        
        # Process map statistics if available
        if 'maps' in match_data and match_data['maps']:
            # First clear existing map statistics
            MapStatistic.query.filter_by(match_id=match.id).delete()
            
            for map_data in match_data['maps']:
                upsert_map_statistic(match.id, map_data)
        
        return match
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in upsert_match: {str(e)}")
        return None


def upsert_map_statistic(match_id, map_data):
    """
    Insert a map statistic in the database
    
    Args:
        match_id (str): Match ID
        map_data (dict): Map statistics data
        
    Returns:
        MapStatistic: The inserted map statistic object
    """
    try:
        # Create new map statistic
        map_stat = MapStatistic(
            match_id=match_id,
            map_name=map_data.get('map_name'),
            team1_score=map_data.get('team1_score'),
            team2_score=map_data.get('team2_score'),
            team1_attack=map_data.get('team1_attack'),
            team1_defense=map_data.get('team1_defense'),
            team2_attack=map_data.get('team2_attack'),
            team2_defense=map_data.get('team2_defense')
        )
        
        # Handle player stats
        if 'player_stats' in map_data and map_data['player_stats']:
            map_stat.player_stats = json.dumps(map_data['player_stats'])
        
        map_stat.last_updated = datetime.utcnow()
        
        # Add to session and commit
        db.session.add(map_stat)
        db.session.commit()
        
        return map_stat
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in upsert_map_statistic: {str(e)}")
        return None


def scrape_and_update_recent_matches(vlr_scraper, bo3_scraper, limit=20):
    """
    Scrape recent matches from both sources and update the database
    
    Args:
        vlr_scraper: VLR scraper module
        bo3_scraper: BO3 scraper module
        limit (int): Maximum number of matches to fetch from each source
        
    Returns:
        int: Number of matches updated
    """
    try:
        updated_count = 0
        
        # Get matches from VLR.gg
        logger.info("Fetching matches from VLR.gg")
        vlr_matches = vlr_scraper.get_matches(limit=limit)
        logger.info(f"Found {len(vlr_matches)} matches on VLR.gg")
        
        for match_data in vlr_matches:
            try:
                match_id = match_data.get('id')
                if not match_id:
                    logger.error("Match data missing ID: %s", match_data)
                    continue
                    
                logger.info(f"Processing match ID: {match_id}")
                
                # Get detailed match information
                match_details = vlr_scraper.get_match_details(match_id)
                
                if not match_details:
                    logger.error(f"Failed to get details for match {match_id}")
                    continue
                    
                logger.info(f"Got details for match {match_id}, team1: {match_details.get('team1_name')}, team2: {match_details.get('team2_name')}")
                
                result = upsert_match(match_details)
                if result:
                    updated_count += 1
                    logger.info(f"Successfully updated match {match_id}")
                else:
                    logger.error(f"Failed to upsert match {match_id}")
            except Exception as e:
                logger.error(f"Error processing VLR match {match_data.get('id', 'unknown')}: {str(e)}")
                continue
        
        # Get matches from BO3.gg
        logger.info("Fetching matches from BO3.gg")
        bo3_matches = bo3_scraper.get_matches(limit=limit)
        logger.info(f"Found {len(bo3_matches)} matches on BO3.gg")
        
        for match_data in bo3_matches:
            try:
                match_id = match_data.get('id')
                if not match_id:
                    logger.error("Match data missing ID: %s", match_data)
                    continue
                    
                logger.info(f"Processing BO3 match ID: {match_id}")
                
                # Get detailed match information
                match_details = bo3_scraper.get_match_details(match_id)
                
                if not match_details:
                    logger.error(f"Failed to get details for BO3 match {match_id}")
                    continue
                    
                logger.info(f"Got details for BO3 match {match_id}")
                
                result = upsert_match(match_details)
                if result:
                    updated_count += 1
                    logger.info(f"Successfully updated BO3 match {match_id}")
                else:
                    logger.error(f"Failed to upsert BO3 match {match_id}")
            except Exception as e:
                logger.error(f"Error processing BO3 match {match_data.get('id', 'unknown')}: {str(e)}")
                continue
        
        logger.info(f"Updated {updated_count} matches")
        return updated_count
    
    except Exception as e:
        logger.error(f"Error in scrape_and_update_recent_matches: {str(e)}")
        return 0


def update_teams_and_players():
    """
    Update team and player information for teams in the database
    
    Returns:
        int: Number of teams updated
    """
    try:
        from scrapers import vlr_scraper
        from scrapers import player_scraper
        
        updated_count = 0
        player_count = 0
        
        # Get all teams in the database
        teams = Team.query.all()
        
        for team in teams:
            try:
                # Get team details from VLR.gg
                team_details = vlr_scraper.get_team_details(team.id)
                
                # If no players or limited player info in team_details, try dedicated player scraper
                if not team_details or len(team_details.get('players', [])) == 0:
                    logger.info(f"Using dedicated player scraper for team: {team.id}")
                    players = player_scraper.get_team_players(team.id)
                    
                    if players:
                        # Add players to team_details
                        if not team_details:
                            team_details = {
                                'id': team.id,
                                'name': team.name,
                                'region': team.region,
                                'logo_url': team.logo_url,
                                'stats': json.loads(team.stats) if team.stats else {},
                                'players': players
                            }
                        else:
                            team_details['players'] = players
                
                if team_details:
                    result = upsert_team(team_details)
                    if result:
                        updated_count += 1
                        players_added = len(team_details.get('players', []))
                        player_count += players_added
                        logger.info(f"Updated team: {team.name} with {players_added} players")
                        
                        # Fetch detailed player info for each player
                        for player in team_details.get('players', []):
                            try:
                                player_detail = player_scraper.get_player_details(player['id'])
                                if player_detail:
                                    upsert_player(player_detail)
                                    logger.info(f"Updated player details for: {player['name']}")
                            except Exception as e:
                                logger.error(f"Error updating player {player['id']}: {str(e)}")
                    else:
                        logger.warning(f"Failed to update team: {team.name}")
            except Exception as e:
                logger.error(f"Error updating team {team.id}: {str(e)}")
                continue
        
        logger.info(f"Updated {updated_count} teams and {player_count} players")
        return updated_count
    
    except Exception as e:
        logger.error(f"Error in update_teams_and_players: {str(e)}")
        return 0


def upsert_event(event_data):
    """
    Insert or update an event in the database
    
    Args:
        event_data (dict): Event data
        
    Returns:
        Event: The inserted or updated event object
    """
    try:
        event = Event.query.filter_by(id=event_data['id']).first()
        
        if not event:
            # Create new event
            event = Event(
                id=event_data['id'],
                name=event_data['name'],
                region=event_data.get('region'),
                start_date=event_data.get('start_date'),
                end_date=event_data.get('end_date'),
                prize_pool=event_data.get('prize_pool'),
                status=event_data.get('status'),
                event_url=event_data.get('event_url'),
                logo_url=event_data.get('logo_url')
            )
            logger.info(f"Creating new event: {event_data['name']}")
        else:
            # Update existing event
            event.name = event_data['name']
            event.region = event_data.get('region')
            event.start_date = event_data.get('start_date')
            event.end_date = event_data.get('end_date')
            event.prize_pool = event_data.get('prize_pool')
            event.status = event_data.get('status')
            event.event_url = event_data.get('event_url')
            event.logo_url = event_data.get('logo_url')
            logger.info(f"Updating existing event: {event_data['name']}")
        
        event.last_updated = datetime.utcnow()
        
        # Add to session and commit
        db.session.add(event)
        db.session.commit()
        
        return event
    
    except Exception as e:
        db.session.rollback()
        logger.error(f"Error in upsert_event: {str(e)}")
        return None


def update_specific_team(team_id):
    """
    Update a specific team's information and its players
    
    Args:
        team_id (str): ID of the team to update
        
    Returns:
        bool: True if successful, False otherwise
    """
    try:
        from scrapers import vlr_scraper
        from scrapers import player_scraper
        
        # Get the team
        team = Team.query.filter_by(id=team_id).first()
        
        if not team:
            logger.warning(f"Team not found: {team_id}")
            return False
        
        # Get team details
        team_details = vlr_scraper.get_team_details(team.id)
        
        # If no players or limited player info in team_details, try dedicated player scraper
        if not team_details or len(team_details.get('players', [])) == 0:
            logger.info(f"Using dedicated player scraper for team: {team_id}")
            players = player_scraper.get_team_players(team.id)
            
            if players:
                # Add players to team_details
                if not team_details:
                    team_details = {
                        'id': team.id,
                        'name': team.name,
                        'region': team.region,
                        'logo_url': team.logo_url,
                        'stats': json.loads(team.stats) if team.stats else {},
                        'players': players
                    }
                else:
                    team_details['players'] = players
        
        if team_details:
            # Update team
            updated_team = upsert_team(team_details)
            if updated_team:
                logger.info(f"Updated team: {team.name} with {len(team_details.get('players', []))} players")
                
                # Fetch detailed player info for each player
                for player in team_details.get('players', []):
                    try:
                        player_detail = player_scraper.get_player_details(player['id'])
                        if player_detail:
                            upsert_player(player_detail)
                            logger.info(f"Updated player details for: {player['name']}")
                    except Exception as e:
                        logger.error(f"Error updating player {player['id']}: {str(e)}")
                        
                return True
            else:
                logger.warning(f"Failed to update team: {team.name}")
                return False
        else:
            logger.warning(f"Failed to fetch details for team: {team.name}")
            return False
    
    except Exception as e:
        logger.error(f"Error in update_specific_team: {str(e)}")
        return False
