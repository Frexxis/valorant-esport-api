import os
import logging

from flask import Flask, jsonify, request, render_template
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy.orm import DeclarativeBase
from werkzeug.middleware.proxy_fix import ProxyFix

# Set up logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class Base(DeclarativeBase):
    pass


db = SQLAlchemy(model_class=Base)
# Create the app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "valorant-esports-api-dev-key")
app.wsgi_app = ProxyFix(app.wsgi_app, x_proto=1, x_host=1)

# Configure the database
app.config["SQLALCHEMY_DATABASE_URI"] = os.environ.get("DATABASE_URL")
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {
    "pool_recycle": 300,
    "pool_pre_ping": True,
}

# Initialize the app with the extension
db.init_app(app)

with app.app_context():
    # Import models
    from models import Player, Team, Match, MapStatistic, Event
    
    # Create tables
    db.create_all()
    
    # Import and setup scheduler
    from utils.scheduling import start_scheduler
    import threading
    
    # Start the scheduler for periodic data updates in a background thread
    scheduler_thread = threading.Thread(target=start_scheduler)
    scheduler_thread.daemon = True  # Make thread a daemon so it exits when main thread exits
    scheduler_thread.start()


# API Rate limiting (simple implementation)
from datetime import datetime, timedelta
from flask import abort

# Simple in-memory rate limiting
request_count = {}
RATE_LIMIT = 60  # Requests per minute
RATE_WINDOW = 60  # Window size in seconds

def check_rate_limit():
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


# Web routes
@app.route('/')
def home():
    return render_template('index.html')

@app.route('/docs')
def docs():
    return render_template('docs.html')


# API routes - These routes are now defined in app_routes.py to avoid conflicts
# @app.route('/api/players', methods=['GET'])
# def get_players():
#     if not check_rate_limit():
#         return jsonify({"error": "Rate limit exceeded"}), 429
#     
#     try:
#         from models import Player
#         
#         # Get query parameters
#         team_id = request.args.get('team_id')
#         limit = request.args.get('limit', 50, type=int)
#         offset = request.args.get('offset', 0, type=int)
#         
#         query = Player.query
#         
#         # Apply filters
#         if team_id:
#             query = query.filter_by(team_id=team_id)
#         
#         # Apply pagination
#         players = query.limit(limit).offset(offset).all()
#         
#         # Convert to dictionary
#         result = [player.to_dict() for player in players]
#         
#         return jsonify(result)
#     
#     except Exception as e:
#         logger.error(f"Error in get_players: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# @app.route('/api/players/<player_id>', methods=['GET'])
# def get_player(player_id):
#     if not check_rate_limit():
#         return jsonify({"error": "Rate limit exceeded"}), 429
#     
#     try:
#         from models import Player
#         
#         player = Player.query.filter_by(id=player_id).first()
#         
#         if not player:
#             return jsonify({"error": "Player not found"}), 404
#         
#         return jsonify(player.to_dict())
#     
#     except Exception as e:
#         logger.error(f"Error in get_player: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# @app.route('/api/teams', methods=['GET'])
# def get_teams():
#     if not check_rate_limit():
#         return jsonify({"error": "Rate limit exceeded"}), 429
#     
#     try:
#         from models import Team
#         
#         # Get query parameters
#         region = request.args.get('region')
#         limit = request.args.get('limit', 50, type=int)
#         offset = request.args.get('offset', 0, type=int)
#         
#         query = Team.query
#         
#         # Apply filters
#         if region:
#             query = query.filter_by(region=region)
#         
#         # Apply pagination
#         teams = query.limit(limit).offset(offset).all()
#         
#         # Convert to dictionary
#         result = [team.to_dict() for team in teams]
#         
#         return jsonify(result)
#     
#     except Exception as e:
#         logger.error(f"Error in get_teams: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# @app.route('/api/teams/<team_id>', methods=['GET'])
# def get_team(team_id):
#     if not check_rate_limit():
#         return jsonify({"error": "Rate limit exceeded"}), 429
#     
#     try:
#         from models import Team
#         
#         team = Team.query.filter_by(id=team_id).first()
#         
#         if not team:
#             return jsonify({"error": "Team not found"}), 404
#         
#         return jsonify(team.to_dict(include_players=True))
#     
#     except Exception as e:
#         logger.error(f"Error in get_team: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# @app.route('/api/matches', methods=['GET'])
# def get_matches():
#     if not check_rate_limit():
#         return jsonify({"error": "Rate limit exceeded"}), 429
#     
#     try:
#         from models import Match
#         
#         # Get query parameters
#         team_id = request.args.get('team_id')
#         status = request.args.get('status')  # upcoming, completed, live
#         limit = request.args.get('limit', 50, type=int)
#         offset = request.args.get('offset', 0, type=int)
#         
#         query = Match.query
#         
#         # Apply filters
#         if team_id:
#             query = query.filter((Match.team1_id == team_id) | (Match.team2_id == team_id))
#         
#         if status:
#             query = query.filter_by(status=status)
#         
#         # Sort by date (most recent first)
#         query = query.order_by(Match.date.desc())
#         
#         # Apply pagination
#         matches = query.limit(limit).offset(offset).all()
#         
#         # Convert to dictionary
#         result = [match.to_dict() for match in matches]
#         
#         return jsonify(result)
#     
#     except Exception as e:
#         logger.error(f"Error in get_matches: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# @app.route('/api/matches/<match_id>', methods=['GET'])
# def get_match(match_id):
#     if not check_rate_limit():
#         return jsonify({"error": "Rate limit exceeded"}), 429
#     
#     try:
#         from models import Match
#         
#         match = Match.query.filter_by(id=match_id).first()
#         
#         if not match:
#             return jsonify({"error": "Match not found"}), 404
#         
#         return jsonify(match.to_dict(include_maps=True))
#     
#     except Exception as e:
#         logger.error(f"Error in get_match: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# @app.route('/api/events', methods=['GET'])
# def get_events():
#     if not check_rate_limit():
#         return jsonify({"error": "Rate limit exceeded"}), 429
#     
#     try:
#         from models import Event
#         
#         # Get query parameters
#         region = request.args.get('region')
#         status = request.args.get('status')  # ongoing, upcoming, completed
#         limit = request.args.get('limit', 20, type=int)
#         offset = request.args.get('offset', 0, type=int)
#         
#         query = Event.query
#         
#         # Apply filters
#         if region:
#             query = query.filter_by(region=region)
#         
#         if status:
#             query = query.filter_by(status=status)
#         
#         # Apply pagination
#         events = query.limit(limit).offset(offset).all()
#         
#         # Convert to dictionary
#         result = [event.to_dict() for event in events]
#         
#         return jsonify(result)
#     
#     except Exception as e:
#         logger.error(f"Error in get_events: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# @app.route('/api/events/<event_id>', methods=['GET'])
# def get_event(event_id):
#     if not check_rate_limit():
#         return jsonify({"error": "Rate limit exceeded"}), 429
#     
#     try:
#         from models import Event
#         
#         event = Event.query.filter_by(id=event_id).first()
#         
#         if not event:
#             return jsonify({"error": "Event not found"}), 404
#         
#         return jsonify(event.to_dict())
#     
#     except Exception as e:
#         logger.error(f"Error in get_event: {str(e)}")
#         return jsonify({"error": str(e)}), 500


# Error handlers
@app.errorhandler(404)
def not_found_error(error):
    return jsonify({"error": "Resource not found"}), 404

@app.errorhandler(500)
def internal_error(error):
    logger.error(f"Server error: {str(error)}")
    return jsonify({"error": "Internal server error"}), 500
