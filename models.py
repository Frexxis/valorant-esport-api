from app import db
from datetime import datetime
import json

class Player(db.Model):
    __tablename__ = 'players'
    
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    team_id = db.Column(db.String(64), db.ForeignKey('teams.id'))
    role = db.Column(db.String(64))
    country = db.Column(db.String(64))
    stats = db.Column(db.Text)  # JSON string of player statistics
    image_url = db.Column(db.String(256))  # Player image URL
    agent_pool = db.Column(db.Text)  # JSON string of player's most played agents
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    team = db.relationship('Team', back_populates='players')
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'team_id': self.team_id,
            'team_name': self.team.name if self.team else None,
            'role': self.role,
            'country': self.country,
            'image_url': self.image_url,
            'agent_pool': json.loads(self.agent_pool) if self.agent_pool else [],
            'stats': json.loads(self.stats) if self.stats else {},
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class Team(db.Model):
    __tablename__ = 'teams'
    
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    region = db.Column(db.String(64))
    logo_url = db.Column(db.String(256))
    stats = db.Column(db.Text)  # JSON string of team statistics
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    players = db.relationship('Player', back_populates='team')
    team1_matches = db.relationship('Match', foreign_keys='Match.team1_id', back_populates='team1')
    team2_matches = db.relationship('Match', foreign_keys='Match.team2_id', back_populates='team2')
    
    def to_dict(self, include_players=False):
        result = {
            'id': self.id,
            'name': self.name,
            'region': self.region,
            'logo_url': self.logo_url,
            'stats': json.loads(self.stats) if self.stats else {},
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
        
        if include_players:
            result['players'] = [player.to_dict() for player in self.players]
        
        return result


class Match(db.Model):
    __tablename__ = 'matches'
    
    id = db.Column(db.String(64), primary_key=True)
    team1_id = db.Column(db.String(64), db.ForeignKey('teams.id'))
    team2_id = db.Column(db.String(64), db.ForeignKey('teams.id'))
    date = db.Column(db.DateTime)
    event_id = db.Column(db.String(64), db.ForeignKey('events.id'), nullable=True)
    event_name = db.Column(db.String(128))
    status = db.Column(db.String(32))  # upcoming, live, completed
    score = db.Column(db.String(16))
    match_url = db.Column(db.String(256))
    match_format = db.Column(db.String(32))  # bo1, bo3, bo5
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    team1 = db.relationship('Team', foreign_keys=[team1_id], back_populates='team1_matches')
    team2 = db.relationship('Team', foreign_keys=[team2_id], back_populates='team2_matches')
    map_statistics = db.relationship('MapStatistic', back_populates='match')
    event = db.relationship('Event', foreign_keys=[event_id])
    
    def to_dict(self, include_maps=False):
        result = {
            'id': self.id,
            'team1': {
                'id': self.team1_id,
                'name': self.team1.name if self.team1 else None
            },
            'team2': {
                'id': self.team2_id,
                'name': self.team2.name if self.team2 else None
            },
            'date': self.date.isoformat() if self.date else None,
            'event_name': self.event_name,
            'event_id': self.event_id,
            'status': self.status,
            'score': self.score,
            'match_url': self.match_url,
            'match_format': self.match_format,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
        
        if include_maps:
            result['maps'] = [map_stat.to_dict() for map_stat in self.map_statistics]
        
        return result


class Event(db.Model):
    __tablename__ = 'events'
    
    id = db.Column(db.String(64), primary_key=True)
    name = db.Column(db.String(128), nullable=False)
    region = db.Column(db.String(64))
    start_date = db.Column(db.DateTime)
    end_date = db.Column(db.DateTime)
    prize_pool = db.Column(db.String(64))
    status = db.Column(db.String(32))  # ongoing, upcoming, completed
    event_url = db.Column(db.String(256))
    logo_url = db.Column(db.String(256))
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'region': self.region,
            'start_date': self.start_date.isoformat() if self.start_date else None,
            'end_date': self.end_date.isoformat() if self.end_date else None,
            'prize_pool': self.prize_pool,
            'status': self.status,
            'event_url': self.event_url,
            'logo_url': self.logo_url,
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }


class MapStatistic(db.Model):
    __tablename__ = 'map_statistics'
    
    id = db.Column(db.Integer, primary_key=True)
    match_id = db.Column(db.String(64), db.ForeignKey('matches.id'))
    map_name = db.Column(db.String(64))
    team1_score = db.Column(db.Integer)
    team2_score = db.Column(db.Integer)
    team1_attack = db.Column(db.Integer)
    team1_defense = db.Column(db.Integer)
    team2_attack = db.Column(db.Integer)
    team2_defense = db.Column(db.Integer)
    player_stats = db.Column(db.Text)  # JSON string of player statistics for this map
    last_updated = db.Column(db.DateTime, default=datetime.utcnow)
    
    match = db.relationship('Match', back_populates='map_statistics')
    
    def to_dict(self):
        return {
            'id': self.id,
            'match_id': self.match_id,
            'map_name': self.map_name,
            'team1_score': self.team1_score,
            'team2_score': self.team2_score,
            'team1_attack': self.team1_attack,
            'team1_defense': self.team1_defense,
            'team2_attack': self.team2_attack,
            'team2_defense': self.team2_defense,
            'player_stats': json.loads(self.player_stats) if self.player_stats else {},
            'last_updated': self.last_updated.isoformat() if self.last_updated else None
        }
