import logging
from flask import jsonify, request
from models import Team, Player, Match, MapStatistic, Event
from utils.db_operations import update_specific_team, upsert_event
from datetime import datetime, timedelta
import json

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# API Rate limiting (simple implementation)
request_count = {}
RATE_LIMIT = 60  # Requests per minute
RATE_WINDOW = 60  # Window size in seconds

def register_routes(app):
    """
    Register all API routes with the Flask app
    
    Args:
        app: Flask application instance
    """
    # Register all routes
    app.add_url_rule('/api/players', 'get_players_extended', get_players_extended, methods=['GET'])
    app.add_url_rule('/api/players/<player_id>', 'get_player_details', get_player_details, methods=['GET'])
    app.add_url_rule('/api/teams', 'get_teams', get_teams, methods=['GET'])
    app.add_url_rule('/api/teams/<team_id>', 'get_team_detail', get_team_detail, methods=['GET'])
    app.add_url_rule('/api/matches', 'get_matches_all', get_matches_all, methods=['GET'])
    app.add_url_rule('/api/matches/live', 'get_live_matches', get_live_matches, methods=['GET'])
    app.add_url_rule('/api/matches/upcoming', 'get_upcoming_matches', get_upcoming_matches, methods=['GET'])
    app.add_url_rule('/api/matches/recent', 'get_recent_matches', get_recent_matches, methods=['GET'])
    app.add_url_rule('/api/matches/<match_id>', 'get_match_detail', get_match_detail, methods=['GET'])
    app.add_url_rule('/api/events', 'get_events', get_events, methods=['GET'])
    app.add_url_rule('/api/events/<event_id>', 'get_event_detail', get_event_detail, methods=['GET'])
    app.add_url_rule('/api/search/teams', 'search_teams', search_teams, methods=['GET'])
    app.add_url_rule('/api/search/players', 'search_players', search_players, methods=['GET'])

def check_rate_limit():
    """
    Check if the current request exceeds the rate limit
    
    Returns:
        bool: True if request is allowed, False otherwise
    """
    ip = request.remote_addr
    now = datetime.now()
    
    # Initialize or clean up old entries
    if ip not in request_count:
        request_count[ip] = []
    
    # Remove entries older than the rate window
    request_count[ip] = [time for time in request_count[ip] if time > now - timedelta(seconds=RATE_WINDOW)]
    
    # Check if rate limit is exceeded
    if len(request_count[ip]) >= RATE_LIMIT:
        return False
    
    # Add current request timestamp
    request_count[ip].append(now)
    return True


# Web routes - commented out to avoid conflict with app.py
# @app.route('/')
# def home_route():
#     from flask import render_template
#     return render_template('index.html')


# @app.route('/docs')
# def docs_route():
#     from flask import render_template
#     return render_template('docs.html')


# API routes
# @app.route('/api/players_extended', methods=['GET'])
def get_players_extended():
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        # Get query parameters
        team_id = request.args.get('team_id')
        role = request.args.get('role')
        country = request.args.get('country')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = Player.query
        
        # Apply filters
        if team_id:
            query = query.filter_by(team_id=team_id)
        
        if role:
            query = query.filter_by(role=role)
            
        if country:
            query = query.filter_by(country=country)
        
        # Apply pagination
        players = query.limit(limit).offset(offset).all()
        
        # Convert to dictionary
        result = [player.to_dict() for player in players]
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_players: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/players_detail/<player_id>', methods=['GET'])
def get_player_details(player_id):
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        player = Player.query.filter_by(id=player_id).first()
        
        if not player:
            return jsonify({"error": "Player not found"}), 404
        
        return jsonify(player.to_dict())
    
    except Exception as e:
        logger.error(f"Error in get_player: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/teams', methods=['GET'])
def get_teams():
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        # Get query parameters
        region = request.args.get('region')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = Team.query
        
        # Apply filters
        if region:
            query = query.filter_by(region=region)
        
        # Apply pagination
        teams = query.limit(limit).offset(offset).all()
        
        # Convert to dictionary
        result = [team.to_dict() for team in teams]
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_teams: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/teams_detail/<team_id>', methods=['GET'])
def get_team_detail(team_id):
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        team = Team.query.filter_by(id=team_id).first()
        
        if not team:
            return jsonify({"error": "Team not found"}), 404
        
        # Fetch latest data from VLR.gg
        refresh = request.args.get('refresh', 'false').lower() == 'true'
        if refresh:
            logger.info(f"Refreshing team data for {team_id}")
            success = update_specific_team(team_id)
            if success:
                # Reload the team from the database
                team = Team.query.filter_by(id=team_id).first()
                logger.info(f"Team data refreshed successfully for {team_id}")
            else:
                logger.warning(f"Failed to refresh team data for {team_id}")
        
        include_players = request.args.get('include_players', 'true').lower() == 'true'
        return jsonify(team.to_dict(include_players=include_players))
    
    except Exception as e:
        logger.error(f"Error in get_team: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/matches_all', methods=['GET'])
def get_matches_all():
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        # Get query parameters
        team_id = request.args.get('team_id')
        status = request.args.get('status')  # upcoming, completed, live
        event = request.args.get('event')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = Match.query
        
        # Apply filters
        if team_id:
            query = query.filter((Match.team1_id == team_id) | (Match.team2_id == team_id))
        
        if status:
            query = query.filter_by(status=status)
            
        if event:
            query = query.filter(Match.event_name.ilike(f"%{event}%"))
        
        # Sort by date (most recent first)
        query = query.order_by(Match.date.desc())
        
        # Apply pagination
        matches = query.limit(limit).offset(offset).all()
        
        # Convert to dictionary
        result = [match.to_dict() for match in matches]
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_matches: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/matches/live', methods=['GET'])
def get_live_matches():
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        # Get only live matches
        query = Match.query.filter_by(status='live')
        
        # Sort by most recent first
        query = query.order_by(Match.date.desc())
        
        # Get matches
        matches = query.all()
        
        # Convert to dictionary
        result = [match.to_dict() for match in matches]
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_live_matches: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/matches/upcoming', methods=['GET'])
def get_upcoming_matches():
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        # Get current time
        now = datetime.utcnow()
        
        # Get matches that are scheduled for future dates
        query = Match.query.filter(Match.date > now)
        
        # Sort by date (closest first)
        query = query.order_by(Match.date.asc())
        
        # Get limit parameter
        limit = request.args.get('limit', 10, type=int)
        
        # Get matches
        matches = query.limit(limit).all()
        
        # Convert to dictionary
        result = [match.to_dict() for match in matches]
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_upcoming_matches: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/matches/recent', methods=['GET'])
def get_recent_matches():
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        # Get current time
        now = datetime.utcnow()
        
        # Get matches that have already happened
        query = Match.query.filter(Match.date <= now)
        
        # Sort by date (most recent first)
        query = query.order_by(Match.date.desc())
        
        # Get limit parameter
        limit = request.args.get('limit', 10, type=int)
        
        # Get matches
        matches = query.limit(limit).all()
        
        # Convert to dictionary
        result = [match.to_dict() for match in matches]
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_recent_matches: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/matches_detail/<match_id>', methods=['GET'])
def get_match_detail(match_id):
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        match = Match.query.filter_by(id=match_id).first()
        
        if not match:
            return jsonify({"error": "Match not found"}), 404
        
        include_maps = request.args.get('include_maps', 'true').lower() == 'true'
        return jsonify(match.to_dict(include_maps=include_maps))
    
    except Exception as e:
        logger.error(f"Error in get_match: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/events', methods=['GET'])
def get_events():
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        # Get query parameters
        region = request.args.get('region')
        status = request.args.get('status')
        limit = request.args.get('limit', 50, type=int)
        offset = request.args.get('offset', 0, type=int)
        
        query = Event.query
        
        # Apply filters
        if region:
            query = query.filter_by(region=region)
            
        if status:
            query = query.filter_by(status=status)
        
        # Apply pagination
        events = query.limit(limit).offset(offset).all()
        
        # If no events in database, fetch from VLR.gg
        if not events:
            from scrapers import vlr_scraper
            
            # Get events from VLR.gg
            vlr_events = vlr_scraper.get_events(limit=limit)
            
            # Store events in database
            for event_data in vlr_events:
                from utils.db_operations import upsert_event
                upsert_event(event_data)
            
            # Retry query
            events = query.limit(limit).offset(offset).all()
        
        # Convert to dictionary
        result = [event.to_dict() for event in events]
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_events: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/events_detail/<event_id>', methods=['GET'])
def get_event_detail(event_id):
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        event = Event.query.filter_by(id=event_id).first()
        
        if not event:
            # Try to fetch from VLR.gg
            from scrapers import vlr_scraper
            from utils.db_operations import upsert_event
            
            event_data = vlr_scraper.get_event_details(event_id)
            
            if event_data:
                event = upsert_event(event_data)
            else:
                return jsonify({"error": "Event not found"}), 404
        
        include_matches = request.args.get('include_matches', 'false').lower() == 'true'
        
        result = event.to_dict()
        
        if include_matches:
            matches = Match.query.filter_by(event_id=event_id).all()
            result['matches'] = [match.to_dict(include_maps=False) for match in matches]
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in get_event: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/search/teams', methods=['GET'])
def search_teams():
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        # Get query parameter
        query = request.args.get('q')
        
        if not query or len(query) < 2:
            return jsonify({"error": "Search query too short"}), 400
        
        # Search in database first
        db_teams = Team.query.filter(Team.name.ilike(f"%{query}%")).limit(10).all()
        
        # Convert to dictionary
        result = [team.to_dict() for team in db_teams]
        
        # If not enough results, search VLR.gg
        if len(result) < 5:
            from scrapers import vlr_scraper
            
            # Get teams from VLR.gg
            vlr_teams = vlr_scraper.search_teams(query, limit=10)
            
            # Add teams from VLR that aren't already in the results
            existing_ids = [team['id'] for team in result]
            for team in vlr_teams:
                if team['id'] not in existing_ids:
                    result.append(team)
                    existing_ids.append(team['id'])
                    
                    # Stop once we have 10 results
                    if len(result) >= 10:
                        break
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in search_teams: {str(e)}")
        return jsonify({"error": str(e)}), 500


@app.route('/api/search/players', methods=['GET'])
def search_players():
    if not check_rate_limit():
        return jsonify({"error": "Rate limit exceeded"}), 429
    
    try:
        # Get query parameter
        query = request.args.get('q')
        
        if not query or len(query) < 2:
            return jsonify({"error": "Search query too short"}), 400
        
        # Search in database first
        db_players = Player.query.filter(Player.name.ilike(f"%{query}%")).limit(10).all()
        
        # Convert to dictionary
        result = [player.to_dict() for player in db_players]
        
        # If not enough results, search VLR.gg
        if len(result) < 5:
            from scrapers import player_scraper
            
            # Get players from VLR.gg
            vlr_players = player_scraper.search_players(query, limit=10)
            
            # Add players from VLR that aren't already in the results
            existing_ids = [player['id'] for player in result]
            for player in vlr_players:
                if player['id'] not in existing_ids:
                    result.append(player)
                    existing_ids.append(player['id'])
                    
                    # Stop once we have 10 results
                    if len(result) >= 10:
                        break
        
        return jsonify(result)
    
    except Exception as e:
        logger.error(f"Error in search_players: {str(e)}")
        return jsonify({"error": str(e)}), 500


# Error handlers commented out to avoid conflict with app.py
# @app.errorhandler(404)
# def not_found_error_route(error):
#     return jsonify({"error": "Resource not found"}), 404
# 
# @app.errorhandler(500)
# def internal_error_route(error):
#     logger.error(f"Server error: {str(error)}")
#     return jsonify({"error": "Internal server error"}), 500